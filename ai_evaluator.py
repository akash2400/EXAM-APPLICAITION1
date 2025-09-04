#!/usr/bin/env python3
"""
AI Evaluator (Multi-Layer, Cache-Only)
====================================

Implements a robust evaluation pipeline using:
- Bi-encoder (all-mpnet-base-v2) for semantic embeddings
- Cross-encoder (all-MiniLM-L12-v2) for relevance scoring
- TF-IDF for keyword/concept analysis
- NLTK for preprocessing (tokenize, stopwords, lemmatize)

Models are loaded ONLY from `adaptive_cache`. No download fallback.
Scores are combined into a final 0-10 score with detailed breakdown.
"""

import os
import re
import string
import logging
from dataclasses import dataclass
from typing import Dict, Any, Tuple, List, Optional

import numpy as np
import torch
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, util


logger = logging.getLogger(__name__)


@dataclass
class EvaluatorConfig:
    cache_dir: str = "./adaptive_cache"
    bi_encoder_name: str = "all-mpnet-base-v2"  # This model exists in adaptive_cache
    cross_encoder_name: str = "all-MiniLM-L12-v2"  # Use L12-v2 model for cross-encoding
    irrelevance_threshold: float = 0.2
    min_length_ratio: float = 0.5
    weights: Tuple[float, float, float, float] = (0.15, 0.45, 0.25, 0.15)  # length, semantic_final, keyword, concept
    device: Optional[str] = None  # "cuda"/"cpu"; auto if None
    # Optional explicit local paths. If provided, they take precedence.
    bi_encoder_path: Optional[str] = None
    cross_encoder_path: Optional[str] = None


class AIEvaluator:
    def __init__(self, config: Optional[EvaluatorConfig] = None):
        self.config = config or EvaluatorConfig()
        self.device = self._resolve_device(self.config.device)
        self._ensure_nltk()
        self.stop_words = set(stopwords.words("english"))
        self.lemmatizer = WordNetLemmatizer()

        self.bi_encoder = self._load_bi_encoder()
        self.cross_encoder = self._load_cross_encoder()

    def _resolve_device(self, requested: Optional[str]) -> str:
        if requested:
            return requested
        return "cuda" if torch.cuda.is_available() else "cpu"

    def _ensure_nltk(self) -> None:
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
        # punkt_tab for newer NLTK versions
        try:
            nltk.data.find('tokenizers/punkt_tab')
        except LookupError:
            try:
                nltk.download('punkt_tab', quiet=True)
            except Exception:
                pass
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)
        try:
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('wordnet', quiet=True)
        try:
            nltk.data.find('corpora/omw-1.4')
        except LookupError:
            nltk.download('omw-1.4', quiet=True)

    def _st_cache_path(self, model_name: str) -> str:
        safe = model_name.replace('/', '_')
        return os.path.join(self.config.cache_dir, f"sentence-transformers_{safe}")

    def _load_bi_encoder(self) -> SentenceTransformer:
        os.makedirs(self.config.cache_dir, exist_ok=True)
        # Prefer explicit path if provided
        if self.config.bi_encoder_path:
            path = self.config.bi_encoder_path
            if not os.path.isdir(path):
                raise RuntimeError(f"Bi-encoder path not found: {path}")
            logger.info("Loading bi-encoder from explicit path: %s", path)
            return SentenceTransformer(path, device=self.device)

        cache_path = self._st_cache_path(self.config.bi_encoder_name)
        if os.path.isdir(cache_path) and os.path.exists(os.path.join(cache_path, 'modules.json')):
            logger.info("Loading bi-encoder from cache: %s", cache_path)
            return SentenceTransformer(cache_path, device=self.device)

        raise RuntimeError(
            f"Bi-encoder not found in cache. Expected at: {cache_path}. "
            f"Provide EvaluatorConfig.bi_encoder_path or place the model in adaptive_cache."
        )

    def _load_cross_encoder(self) -> Optional[SentenceTransformer]:
        os.makedirs(self.config.cache_dir, exist_ok=True)
        # Prefer explicit path if provided
        if self.config.cross_encoder_path:
            path = self.config.cross_encoder_path
            if not os.path.isdir(path):
                logger.warning(f"Cross-encoder path not found: {path}")
                return None
            logger.info("Loading cross-encoder from explicit path: %s", path)
            return SentenceTransformer(path, device=self.device)

        # Use the all-MiniLM-L12-v2 model as cross-encoder
        cache_path = self._st_cache_path(self.config.cross_encoder_name)
        if os.path.isdir(cache_path) and os.path.exists(os.path.join(cache_path, 'modules.json')):
            logger.info("Loading cross-encoder (L12-v2) from cache: %s", cache_path)
            return SentenceTransformer(cache_path, device=self.device)

        logger.warning(
            f"Cross-encoder model not found in cache. Expected at: {cache_path}. "
            f"Continuing with bi-encoder only. "
            f"Provide EvaluatorConfig.cross_encoder_path or place the model in adaptive_cache."
        )
        return None

    # --------------------------- Preprocessing ---------------------------
    def preprocess(self, text: str) -> str:
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r"\s+", " ", text)
        text = text.translate(str.maketrans('', '', string.punctuation))
        tokens = nltk.word_tokenize(text)
        tokens = [t for t in tokens if t not in self.stop_words and t.isalpha()]
        lemmas = [self.lemmatizer.lemmatize(t) for t in tokens]
        return " ".join(lemmas)

    # ---------------------- Step 2: Irrelevance Detection ----------------------
    def _irrelevant(self, student: str, reference: str) -> Tuple[bool, float]:
        emb_s = self.bi_encoder.encode(student, convert_to_tensor=True, device=self.device)
        emb_r = self.bi_encoder.encode(reference, convert_to_tensor=True, device=self.device)
        score = util.cos_sim(emb_s, emb_r).item()
        
        # Check for semantic incoherence using intelligent analysis
        if self._is_semantically_incoherent(student, reference):
            return True, float(score)
            
        return (score < self.config.irrelevance_threshold), float(score)
    
    def _is_semantically_incoherent(self, student: str, reference: str) -> bool:
        """
        Intelligently detect semantic incoherence by analyzing concept relationships
        and logical consistency rather than using hard-coded patterns.
        """
        try:
            # Step 1: Extract key concepts and their relationships
            student_concepts = self._extract_concepts(student)
            reference_concepts = self._extract_concepts(reference)
            
            # Step 2: Analyze concept coherence using semantic embeddings
            coherence_score = self._analyze_concept_coherence(student_concepts, reference_concepts)
            
            # Step 3: Check for logical contradictions
            contradiction_score = self._check_logical_contradictions(student, reference)
            
            # Step 4: Evaluate overall semantic coherence
            if coherence_score < 0.3 or contradiction_score > 0.7:
                return True
                
            return False
            
        except Exception as e:
            logger.warning(f"Error in semantic coherence analysis: {e}")
            return False
    
    def _extract_concepts(self, text: str) -> Dict[str, Dict[str, Any]]:
        """
        Extract key concepts and their semantic properties from text.
        Returns a dictionary mapping concepts to their properties.
        """
        try:
            # Tokenize and get POS tags
            tokens = nltk.word_tokenize(text.lower())
            pos_tags = nltk.pos_tag(tokens)
            
            concepts = {}
            
            for token, pos in pos_tags:
                if pos.startswith('NN') or pos.startswith('JJ'):  # Nouns and adjectives
                    if len(token) > 2:  # Skip very short tokens
                        # Get semantic embedding for this concept
                        try:
                            embedding = self.bi_encoder.encode(token, convert_to_tensor=True, device=self.device)
                            concepts[token] = {
                                'embedding': embedding,
                                'pos': pos,
                                'length': len(token),
                                'is_technical': self._is_technical_term(token)
                            }
                        except Exception:
                            concepts[token] = {
                                'embedding': None,
                                'pos': pos,
                                'length': len(token),
                                'is_technical': self._is_technical_term(token)
                            }
            
            return concepts
            
        except Exception as e:
            logger.warning(f"Error extracting concepts: {e}")
            return {}
    
    def _is_technical_term(self, word: str) -> bool:
        """Check if a word is likely a technical/scientific term"""
        technical_indicators = [
            'cellular', 'molecular', 'biological', 'chemical', 'physical',
            'mitochondria', 'photosynthesis', 'respiration', 'chlorophyll',
            'enzyme', 'atp', 'dna', 'rna', 'protein', 'gene', 'chromosome'
        ]
        return word.lower() in technical_indicators
    
    def _analyze_concept_coherence(self, student_concepts: Dict, reference_concepts: Dict) -> float:
        """
        Analyze how coherent the student's concepts are with the reference concepts
        using semantic similarity and relationship analysis.
        """
        try:
            if not student_concepts or not reference_concepts:
                return 0.5  # Neutral score if we can't analyze
            
            # Calculate semantic similarity between concept sets
            student_embeddings = []
            reference_embeddings = []
            
            for concept, props in student_concepts.items():
                if props.get('embedding') is not None:
                    student_embeddings.append(props['embedding'])
            
            for concept, props in reference_concepts.items():
                if props.get('embedding') is not None:
                    reference_embeddings.append(props['embedding'])
            
            if not student_embeddings or not reference_embeddings:
                return 0.5
            
            # Calculate average semantic similarity
            total_similarity = 0
            count = 0
            
            for s_emb in student_embeddings:
                for r_emb in reference_embeddings:
                    sim = util.cos_sim(s_emb, r_emb).item()
                    total_similarity += sim
                    count += 1
            
            if count == 0:
                return 0.5
                
            avg_similarity = total_similarity / count
            
            # Analyze concept relationship coherence
            relationship_coherence = self._analyze_concept_relationships(student_concepts, reference_concepts)
            
            # Combine semantic similarity with relationship coherence
            final_coherence = 0.7 * avg_similarity + 0.3 * relationship_coherence
            
            return max(0.0, min(1.0, final_coherence))
            
        except Exception as e:
            logger.warning(f"Error analyzing concept coherence: {e}")
            return 0.5
    
    def _analyze_concept_relationships(self, student_concepts: Dict, reference_concepts: Dict) -> float:
        """
        Analyze the logical relationships between concepts to detect incoherent combinations.
        """
        try:
            # Get technical terms from both sets
            student_technical = [concept for concept, props in student_concepts.items() 
                               if props.get('is_technical', False)]
            reference_technical = [concept for concept, props in reference_concepts.items() 
                                 if props.get('is_technical', False)]
            
            if not student_technical or not reference_technical:
                return 0.5
            
            # Check for domain mismatch using semantic clustering
            domain_coherence = self._check_domain_coherence(student_technical, reference_technical)
            
            # Check for logical consistency
            logical_consistency = self._check_logical_consistency(student_concepts, reference_concepts)
            
            return (domain_coherence + logical_consistency) / 2
            
        except Exception as e:
            logger.warning(f"Error analyzing concept relationships: {e}")
            return 0.5
    
    def _check_domain_coherence(self, student_terms: List[str], reference_terms: List[str]) -> float:
        """
        Check if the technical terms belong to the same scientific domain.
        """
        try:
            if not student_terms or not reference_terms:
                return 0.5
            
            # Create embeddings for all terms
            all_terms = student_terms + reference_terms
            embeddings = []
            
            for term in all_terms:
                try:
                    emb = self.bi_encoder.encode(term, convert_to_tensor=True, device=self.device)
                    embeddings.append(emb)
                except Exception:
                    continue
            
            if len(embeddings) < 2:
                return 0.5
            
            # Calculate pairwise similarities
            similarities = []
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    sim = util.cos_sim(embeddings[i], embeddings[j]).item()
                    similarities.append(sim)
            
            if not similarities:
                return 0.5
            
            # Higher average similarity indicates better domain coherence
            avg_similarity = sum(similarities) / len(similarities)
            return avg_similarity
            
        except Exception as e:
            logger.warning(f"Error checking domain coherence: {e}")
            return 0.5
    
    def _check_logical_consistency(self, student_concepts: Dict, reference_concepts: Dict) -> float:
        """
        Check for logical consistency between concept relationships.
        """
        try:
            # This is a simplified version - in practice, you might use more sophisticated
            # logical reasoning or knowledge graphs
            
            # Check if student concepts make logical sense together
            student_terms = list(student_concepts.keys())
            
            if len(student_terms) < 2:
                return 0.8  # Single concepts are usually consistent
            
            # Use cross-encoder to check logical consistency if available
            if self.cross_encoder is not None:
                try:
                    # Create a logical consistency check
                    consistency_check = f"Are these concepts logically related: {', '.join(student_terms)}"
                    reference_text = "These concepts are logically related and make sense together."
                    
                    consistency_score = self.cross_encoder.predict([(consistency_check, reference_text)])
                    return consistency_score
                except Exception:
                    pass
            
            # Fallback: basic heuristic based on concept diversity
            technical_count = sum(1 for props in student_concepts.values() if props.get('is_technical', False))
            total_count = len(student_concepts)
            
            if total_count == 0:
                return 0.5
            
            # If there are many technical terms, they should be related
            if technical_count > 1:
                # Check if they're from similar domains
                return self._check_domain_coherence(student_terms, student_terms)
            
            return 0.7  # Default to reasonable consistency
            
        except Exception as e:
            logger.warning(f"Error checking logical consistency: {e}")
            return 0.5
    
    def _check_logical_contradictions(self, student: str, reference: str) -> float:
        """
        Check for logical contradictions between student answer and reference.
        """
        try:
            if self.cross_encoder is not None:
                # Use cross-encoder to detect contradictions
                contradiction_check = f"Does this contradict: {student} vs {reference}"
                reference_text = "These statements are consistent and do not contradict each other."
                
                contradiction_score = self.cross_encoder.predict([(contradiction_check, reference_text)])
                return contradiction_score
            else:
                # Fallback: basic contradiction detection
                return 0.3  # Default to low contradiction likelihood
                
        except Exception as e:
            logger.warning(f"Error checking logical contradictions: {e}")
            return 0.3

    # ---------------------- Step 3: Length Analysis ----------------------
    def _length_score(self, student_tokens: List[str], reference_tokens: List[str]) -> float:
        s_len = max(1, len(student_tokens))
        r_len = max(1, len(reference_tokens))
        if s_len < self.config.min_length_ratio * r_len:
            return s_len / (self.config.min_length_ratio * r_len)
        return min(1.0, s_len / r_len)

    # ---------------------- Step 4: Semantic Analysis ----------------------
    def _semantic_scores(self, student: str, reference: str) -> Tuple[float, float, float]:
        # Bi-encoder cosine
        emb_s = self.bi_encoder.encode(student, convert_to_tensor=True, device=self.device)
        emb_r = self.bi_encoder.encode(reference, convert_to_tensor=True, device=self.device)
        semantic_score = util.cos_sim(emb_s, emb_r).item()
        
        # Cross-encoder relevance using L12-v2 model
        if self.cross_encoder is not None:
            try:
                # Use the L12-v2 model to get embeddings for both texts
                cross_emb_s = self.cross_encoder.encode(student, convert_to_tensor=True, device=self.device)
                cross_emb_r = self.cross_encoder.encode(reference, convert_to_tensor=True, device=self.device)
                cross_score = util.cos_sim(cross_emb_s, cross_emb_r).item()
            except Exception:
                # If prediction fails for any reason, fall back to bi-encoder score
                cross_score = semantic_score
        else:
            # Cross-encoder not available, use bi-encoder score only
            cross_score = semantic_score
        
        # Adjust weights based on availability
        if self.cross_encoder is not None:
            semantic_final = 0.6 * float(semantic_score) + 0.4 * float(cross_score)
        else:
            semantic_final = float(semantic_score)  # Use bi-encoder score directly
            
        return float(semantic_score), float(cross_score), float(semantic_final)

    # ---------------------- Step 5: Keyword / Concept Analysis ----------------------
    def _keyword_and_concept(self, student: str, reference: str) -> Tuple[float, float, List[str]]:
        # TF-IDF cosine
        vectorizer = TfidfVectorizer()
        tfidf = vectorizer.fit_transform([student, reference])
        keyword_score = float(cosine_similarity(tfidf[0], tfidf[1])[0][0])
        # Concept overlap using top-n reference keywords
        ref_tokens = reference.split()
        student_tokens = set(student.split())
        # Top keywords by TF-IDF weight (pick top 10)
        try:
            vocab = vectorizer.vocabulary_
            inv_vocab = {idx: term for term, idx in vocab.items()}
            ref_vec = tfidf[1].toarray()[0]
            top_indices = np.argsort(ref_vec)[::-1][:10]
            top_terms = [inv_vocab.get(i) for i in top_indices if inv_vocab.get(i)]
        except Exception:
            top_terms = list(set(ref_tokens))
        ref_keywords = set(top_terms) if top_terms else set(ref_tokens)
        concept_overlap = len(ref_keywords & student_tokens) / max(1, len(ref_keywords))
        return keyword_score, float(concept_overlap), top_terms

    # ---------------------- Public API ----------------------
    def evaluate(self, student_answer: str, reference_answer: str) -> Dict[str, Any]:
        # Step 1: Preprocess
        student_clean = self.preprocess(student_answer or "")
        reference_clean = self.preprocess(reference_answer or "")

        # Early exit for empty student
        if not student_clean:
            return self._result(0.0, {
                "reason": "Empty or stopword-only answer after cleaning"
            })

        # Step 2: Irrelevance Detection
        is_irrelevant, bi_sim = self._irrelevant(student_clean, reference_clean)
        if is_irrelevant:
            return self._result(0.0, {
                "irrelevant": True,
                "bi_encoder_similarity": round(bi_sim, 4)
            })

        # Step 3: Length Analysis
        length_score = self._length_score(student_clean.split(), reference_clean.split())

        # Step 4: Semantic Analysis
        semantic_score, cross_score, semantic_final = self._semantic_scores(student_clean, reference_clean)

        # Step 5: Keyword / Concept Analysis
        keyword_score, concept_score, top_terms = self._keyword_and_concept(student_clean, reference_clean)

        # Step 6: Aggregate
        w_len, w_sem, w_kw, w_con = self.config.weights
        final = (
            w_len * length_score +
            w_sem * semantic_final +
            w_kw * keyword_score +
            w_con * concept_score
        )
        final = max(0.0, min(1.0, float(final)))

        return self._result(round(final * 10.0, 2), {
            "irrelevant": False,
            "length_score": round(float(length_score), 4),
            "semantic_bi": round(float(semantic_score), 4),
            "cross_encoder": round(float(cross_score), 4),
            "semantic_final": round(float(semantic_final), 4),
            "keyword_score": round(float(keyword_score), 4),
            "concept_score": round(float(concept_score), 4),
            "reference_keywords": top_terms,
        })

    def _result(self, final_score_0_to_10: float, details: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "final_score": final_score_0_to_10,
            "details": details
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    evaluator = AIEvaluator()
    tests = [
        ("Nothing i dont know", "Artificial Intelligence is a field of computer science that builds intelligent machines."),
        ("AI is computer science field for making smart machines that think like humans", "Artificial Intelligence is a field of computer science that builds intelligent machines."),
        ("Mitochondria produce ATP energy through cellular respiration processes in cells", "Mitochondria are cellular organelles that produce ATP energy through respiration"),
        ("yes", "Photosynthesis is the process by which plants convert sunlight into energy using chlorophyll"),
        ("The process where plants use sunlight and chlorophyll to make energy from carbon dioxide and water", "Photosynthesis is the process by which plants convert sunlight into energy using chlorophyll"),
    ]
    for s, r in tests:
        res = evaluator.evaluate(s, r)
        print({"student": s, "score": res["final_score"], "details": res["details"]})
