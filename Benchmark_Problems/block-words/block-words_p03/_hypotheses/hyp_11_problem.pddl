
(define (problem blocks_words)
	(:domain blocks)
(:objects 

m o t h e r w a - block
)
(:init
(handempty)
(clear m)
(on m o)
(ontable o)
(clear e)
(ontable e)
(clear t)
(on t w)
(ontable w)
(clear h)
(ontable h)
(clear r)
(on r a)
(ontable a)
)
(:goal (and
(clear t)
(ontable e)
(on t o)
(on o r)
(on r e)
))
)
