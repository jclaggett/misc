(ns misc.constraint
  (:refer-clojure :exclude [range])
  (:use [clojure.core :as core :only []]))

;; Verdict Flags
(def Invalid   #{})                    ; Not matching and don't continue.
(def Continue  #{:continue})           ; Not matching but continue.
(def Matching  #{:matching})           ; Matching but don't continue.
(def Satisfied #{:matching :continue}) ; Matching and continue.

(defn instance
  "Create a new instance of the constraint and manage/hide the state."
  [constraint]
  (let [[state verdict] (constraint)
        wrapped (atom state)]
    [(fn wrapper [token]
       (let [[new-state verdict] (constraint @wrapped token)]
         (reset! wrapped new-state)
         verdict))
     verdict]))

;; Should this always return true/false?  Always :matching/nil? Or is this ok?
(defn match
  "Compare constraint against a list of tokens."
  [constraint tokens]
  (let [[wrapper verdict] (instance constraint)]
    (loop [verdict verdict, tokens tokens]
      (if (empty? tokens)
        (:matching verdict)
        (if (:continue verdict)
          (recur (wrapper (first tokens)) (next tokens))
          ; The previous verdict indicated no continue so this
          ; token stream can never match.
          false)))))



(defn any []
  (fn any-fn
    ([]            [nil Satisfied])
    ([state token] [state Satisfied])))

(defn member-range [min max]
  (fn member-range-fn
    ([] [nil Satisfied])
    ([state token] [state (if (<= min token max) Satisfied Invalid)])))

(defn single []
  (fn single-fn
    ([] [Matching Continue])
    ([state token] [Invalid state])))

(defn between
  "Matched count tokens where: min <= count <= max."
  [min max]
  (fn between-fn
    ([] (between-fn 0 nil))
    ([count token]
     (cond
       (< count min) [(inc count) Continue]
       (nil? max)    [(inc count) Satisfied]
       (= count max) [(inc count) Matching]
       (> count max) [(inc count) Invalid]
       :else         [(inc count) Satisfied]))))





(defn assert-match [constraint tokens]
  (assert (match constraint tokens)))

(defn assert-nomatch [constraint tokens]
  (assert (not (match constraint tokens))))



;(defn test-null []
;  (assert-match (null) [])
;  (assert-nomatch (null) [1]))

(defn test-any []
  (let [c (any)]
    (assert-match c [])
    (assert-match c [1 2 3])
    (assert-match c (take 9 (cycle [1 2 3])))
    (assert-match c (core/range 100))
    (assert-match c "abcdef"))
  :okay)


