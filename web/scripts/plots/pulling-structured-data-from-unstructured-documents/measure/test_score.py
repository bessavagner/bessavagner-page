"""The scorer is the one part of this benchmark with a green/red signal.

The bug this file exists to prevent is the one that shipped three times in
Sprint 09: a metric that is a bare number in a state where nothing was measured.
An F1 of 0.0 for a field nobody predicted is TRUE. An F1 of 0.0 for a field that
does not exist in the corpus is a FABRICATION. They must not look the same.
"""
import unittest

import score


class ScoreField(unittest.TestCase):
    def test_a_perfect_prediction_scores_one(self):
        out = score.score_field(["a@b.com"], ["a@b.com"])
        self.assertEqual(out["precision"], 1.0)
        self.assertEqual(out["recall"], 1.0)
        self.assertEqual(out["f1"], 1.0)

    def test_a_miss_costs_recall_not_precision(self):
        # Predicted nothing, gold had one: recall 0, and precision is UNDEFINED,
        # not 1.0. Nothing was claimed, so nothing was claimed correctly.
        out = score.score_field([], ["a@b.com"])
        self.assertEqual(out["recall"], 0.0)
        self.assertEqual(out["precision"], 0.0)
        self.assertEqual(out["f1"], 0.0)
        self.assertEqual(out["fn"], 1)

    def test_a_wrong_prediction_costs_both(self):
        out = score.score_field(["x@y.com"], ["a@b.com"])
        self.assertEqual(out["tp"], 0)
        self.assertEqual(out["fp"], 1)
        self.assertEqual(out["fn"], 1)
        self.assertEqual(out["f1"], 0.0)

    def test_a_partial_hit_scores_between(self):
        # 1 of 2 predicted correct, 1 of 2 gold found.
        out = score.score_field(["a@b.com", "junk"], ["a@b.com", "c@d.com"])
        self.assertEqual(out["tp"], 1)
        self.assertEqual(out["fp"], 1)
        self.assertEqual(out["fn"], 1)
        self.assertAlmostEqual(out["precision"], 0.5)
        self.assertAlmostEqual(out["recall"], 0.5)
        self.assertAlmostEqual(out["f1"], 0.5)

    def test_matching_is_order_insensitive(self):
        out = score.score_field(["b", "a"], ["a", "b"])
        self.assertEqual(out["f1"], 1.0)

    def test_matching_is_whitespace_and_case_normalised(self):
        # "R$ 1.299,90" and "r$ 1.299,90 " are the same extracted amount. A
        # scorer that says otherwise is measuring its own strictness, not the
        # pipeline.
        out = score.score_field([" A@B.com "], ["a@b.com"])
        self.assertEqual(out["f1"], 1.0)

    def test_a_duplicate_prediction_is_not_two_hits(self):
        # Predicting the same value twice must not double-count as 2 TPs — the
        # pipeline found one fact, not two.
        out = score.score_field(["a@b.com", "a@b.com"], ["a@b.com"])
        self.assertEqual(out["tp"], 1)
        self.assertEqual(out["f1"], 1.0)

    def test_an_empty_gold_and_empty_prediction_is_not_a_score(self):
        # NOTHING WAS MEASURED. There is no F1 here, and 0.0 would be a lie with
        # a number attached — the exact bug class that shipped three times in
        # Sprint 09. The field must be absent from the chart, not plotted at 0.
        out = score.score_field([], [])
        self.assertIsNone(out["f1"])
        self.assertIsNone(out["precision"])
        self.assertIsNone(out["recall"])


class ScoreCorpus(unittest.TestCase):
    GOLD = {
        "doc1": {"email": ["a@b.com"], "total": ["10.00"]},
        "doc2": {"email": ["c@d.com"], "total": ["20.00"]},
    }
    FIELDS = ["email", "total"]

    def test_it_aggregates_across_documents(self):
        preds = {
            "doc1": {"email": ["a@b.com"], "total": ["10.00"]},
            "doc2": {"email": ["c@d.com"], "total": ["99.99"]},
        }
        out = score.score_corpus(preds, self.GOLD, self.FIELDS)
        self.assertEqual(out["email"]["f1"], 1.0)
        self.assertEqual(out["total"]["tp"], 1)
        self.assertEqual(out["total"]["fp"], 1)
        self.assertEqual(out["total"]["fn"], 1)

    def test_a_document_the_pipeline_dropped_counts_as_misses(self):
        # A crashed document must not vanish from the denominator. Silently
        # skipping it would INFLATE the score of the technique that crashed —
        # the benchmark would reward failure.
        preds = {"doc1": {"email": ["a@b.com"], "total": ["10.00"]}}
        out = score.score_corpus(preds, self.GOLD, self.FIELDS)
        self.assertEqual(out["email"]["tp"], 1)
        self.assertEqual(out["email"]["fn"], 1)   # doc2's gold email is a miss
        self.assertAlmostEqual(out["email"]["recall"], 0.5)
