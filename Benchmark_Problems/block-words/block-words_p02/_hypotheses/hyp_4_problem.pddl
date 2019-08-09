
(define (problem blocks_words)
	(:domain blocks)
(:objects 

s t a r h c u k - block
)
(:init
(handempty)
(clear t)
(ontable t)
(clear u)
(ontable u)
(clear r)
(ontable r)
(clear k)
(ontable k)
(clear c)
(ontable c)
(clear s)
(on s a)
(on a h)
(ontable h)
)
(:goal (and
(clear c)
(ontable h)
(on c r)
(on r a)
(on a s)
(on s h)
))
)
