#!/bin/sh
#
# Makefile for FF v 1.0
#


####### FLAGS

TYPE	=
ADDONS	=

CC      = gcc

CFLAGS	= -O6 -Wall -g -ansi $(TYPE) $(ADDONS)
# -g -pg

LIBS    = -lm


####### Files

PDDL_PARSER_SRC	= scan-fct_pddl.tab.c \
	scan-ops_pddl.tab.c \
	scan-probname.tab.c \
	lex.fct_pddl.c \
	lex.ops_pddl.c

PDDL_PARSER_OBJ = scan-fct_pddl.tab.o \
	scan-ops_pddl.tab.o


SOURCES 	= main.c \
	memory.c \
	output.c \
	parse.c \
	expressions.c \
	inst_pre.c \
	inst_easy.c \
	inst_hard.c \
	inst_final.c \
	relax.c \
	search.c \
	utility.c

LIB_SOURCES = libff.c \
	memory.c \
	output.c \
	parse.c \
	expressions.c \
	inst_pre.c \
	inst_easy.c \
	inst_hard.c \
	inst_final.c \
	relax.c \
	search.c \
	utility.c


OBJECTS 	= $(SOURCES:.c=.o)
LIB_OBJECTS	= $(LIB_SOURCES:.c=.o)

####### Implicit rules

.SUFFIXES:

.SUFFIXES: .c .o

.c.o:; $(CC) -c $(CFLAGS) $<

####### Build rules

libff: $(LIB_OBJECTS) $(PDDL_PARSER_OBJ)
	ar cru libff.a $(LIB_OBJECTS) $(PDDL_PARSER_OBJ)

ff: $(OBJECTS) $(PDDL_PARSER_OBJ)
	$(CC) -static -o ff $(OBJECTS) $(PDDL_PARSER_OBJ) $(CFLAGS) $(LIBS)

# pddl syntax
scan-fct_pddl.tab.c: scan-fct_pddl.y lex.fct_pddl.c
	bison -pfct_pddl -bscan-fct_pddl scan-fct_pddl.y

scan-ops_pddl.tab.c: scan-ops_pddl.y lex.ops_pddl.c
	bison -pops_pddl -bscan-ops_pddl scan-ops_pddl.y

lex.fct_pddl.c: lex-fct_pddl.l
	flex -Pfct_pddl lex-fct_pddl.l

lex.ops_pddl.c: lex-ops_pddl.l
	flex -Pops_pddl lex-ops_pddl.l

test_lib: test_main.cxx
	g++ -static -o test_lib test_main.cxx -lff -L./

# misc
clean:
	rm -f *.o *.bak *~ *% core *_pure_p9_c0_400.o.warnings test_lib \
        \#*\# $(RES_PARSER_SRC) $(PDDL_PARSER_SRC)

veryclean: clean
	rm -f ff H* J* K* L* O* graph.* *.symbex gmon.out \
	$(PDDL_PARSER_SRC) \
	lex.fct_pddl.c lex.ops_pddl.c lex.probname.c \
	*.output

depend:
	makedepend -- $(SOURCES)  $(LIB_SOURCES) $(PDDL_PARSER_SRC) test_main.cxx

lint:
	lclint -booltype Bool $(SOURCES) 2> output.lint

# DO NOT DELETE

main.o: ff.h #
# main.o:
# main.o:
# main.o:
# main.o:
# main.o:
# main.o:
# main.o:
# main.o:
# main.o:
# main.o:
# main.o:
# main.o:
# main.o:
main.o:  memory.h  output.h
main.o: parse.h expressions.h inst_pre.h inst_easy.h inst_hard.h inst_final.h#
main.o: relax.h search.h#
# memory.o:
# memory.o:
memory.o:   ff.h
# memory.o:
# memory.o:
# memory.o:
# memory.o:
# memory.o:
# memory.o:
# memory.o:
# memory.o:
# memory.o:
# memory.o:
# memory.o:
memory.o:   memory.h
memory.o: inst_pre.h#
output.o: ff.h #
# output.o:
# output.o:
# output.o:
# output.o:
# output.o:
# output.o:
# output.o:
# output.o:
# output.o:
# output.o:
# output.o:
# output.o:
# output.o:
output.o:   utility.h
output.o: output.h#
parse.o: ff.h #
# parse.o:
# parse.o:
# parse.o:
# parse.o:
# parse.o:
# parse.o:
# parse.o:
# parse.o:
# parse.o:
# parse.o:
# parse.o:
# parse.o:
# parse.o:
parse.o:  memory.h  output.h
parse.o: parse.h#
# expressions.o:
# expressions.o:
expressions.o:   ff.h
# expressions.o:
# expressions.o:
# expressions.o:
# expressions.o:
# expressions.o:
# expressions.o:
# expressions.o:
# expressions.o:
# expressions.o:
# expressions.o:
# expressions.o:
# expressions.o:
expressions.o:   output.h
expressions.o: memory.h expressions.h#
# inst_pre.o:
# inst_pre.o:
inst_pre.o:   ff.h
# inst_pre.o:
# inst_pre.o:
# inst_pre.o:
# inst_pre.o:
# inst_pre.o:
# inst_pre.o:
# inst_pre.o:
# inst_pre.o:
# inst_pre.o:
# inst_pre.o:
# inst_pre.o:
# inst_pre.o:
inst_pre.o:   output.h
inst_pre.o: memory.h expressions.h inst_pre.h#
inst_easy.o: ff.h #
# inst_easy.o:
# inst_easy.o:
# inst_easy.o:
# inst_easy.o:
# inst_easy.o:
# inst_easy.o:
# inst_easy.o:
# inst_easy.o:
# inst_easy.o:
# inst_easy.o:
# inst_easy.o:
# inst_easy.o:
# inst_easy.o:
inst_easy.o:   output.h
inst_easy.o: memory.h expressions.h inst_pre.h#
inst_easy.o: inst_easy.h#
inst_hard.o: ff.h #
# inst_hard.o:
# inst_hard.o:
# inst_hard.o:
# inst_hard.o:
# inst_hard.o:
# inst_hard.o:
# inst_hard.o:
# inst_hard.o:
# inst_hard.o:
# inst_hard.o:
# inst_hard.o:
# inst_hard.o:
# inst_hard.o:
inst_hard.o:   output.h
inst_hard.o: memory.h  expressions.h inst_pre.h
inst_hard.o: inst_hard.h#
inst_final.o: ff.h #
# inst_final.o:
# inst_final.o:
# inst_final.o:
# inst_final.o:
# inst_final.o:
# inst_final.o:
# inst_final.o:
# inst_final.o:
# inst_final.o:
# inst_final.o:
# inst_final.o:
# inst_final.o:
# inst_final.o:
inst_final.o:   output.h
inst_final.o: memory.h expressions.h inst_pre.h
inst_final.o: inst_final.h#
relax.o: ff.h #
# relax.o:
# relax.o:
# relax.o:
# relax.o:
# relax.o:
# relax.o:
# relax.o:
# relax.o:
# relax.o:
# relax.o:
# relax.o:
# relax.o:
# relax.o:
relax.o:  output.h memory.h
relax.o: expressions.h relax.h search.h#
search.o: ff.h #
# search.o:
# search.o:
# search.o:
# search.o:
# search.o:
# search.o:
# search.o:
# search.o:
# search.o:
# search.o:
# search.o:
# search.o:
# search.o:
search.o:   output.h memory.h
search.o:  expressions.h relax.h search.h
# utility.o:
# utility.o:
utility.o:   utility.h
utility.o: ff.h #
# utility.o:
# utility.o:
# utility.o:
# utility.o:
# utility.o:
# utility.o:
# utility.o:
# utility.o:
# utility.o:
# utility.o:
# utility.o:
utility.o:  output.h
 libff.o: libff.h ff.h #
# # libff.o:
# # libff.o:
# # libff.o:
# # libff.o:
# # libff.o:
# # libff.o:
# # libff.o:
# # libff.o:
# # libff.o:
# # libff.o:
# # libff.o:
# # libff.o:
# # libff.o:
libff.o:  memory.h  output.h
libff.o: parse.h expressions.h inst_pre.h inst_easy.h inst_hard.h#
libff.o: inst_final.h#
# # memory.o:
# # memory.o:
memory.o:   ff.h
# # memory.o:
# # memory.o:
# # memory.o:
# # memory.o:
# # memory.o:
# # memory.o:
# # memory.o:
# # memory.o:
# # memory.o:
# # memory.o:
# # memory.o:
memory.o:   memory.h
memory.o: inst_pre.h#
output.o: ff.h #
# # output.o:
# # output.o:
# # output.o:
# # output.o:
# # output.o:
# # output.o:
# # output.o:
# # output.o:
# # output.o:
# # output.o:
# # output.o:
# # output.o:
# # output.o:
output.o:   utility.h
output.o: output.h#
parse.o: ff.h #
# # parse.o:
# # parse.o:
# # parse.o:
# # parse.o:
# # parse.o:
# # parse.o:
# # parse.o:
# # parse.o:
# # parse.o:
# # parse.o:
# # parse.o:
# # parse.o:
# # parse.o:
parse.o:  memory.h  output.h
parse.o: parse.h#
# # expressions.o:
# # expressions.o:
expressions.o:   ff.h
# # expressions.o:
# # expressions.o:
# # expressions.o:
# # expressions.o:
# # expressions.o:
# # expressions.o:
# # expressions.o:
# # expressions.o:
# # expressions.o:
# # expressions.o:
# # expressions.o:
# # expressions.o:
expressions.o:   output.h
expressions.o: memory.h expressions.h#
# # inst_pre.o:
# # inst_pre.o:
inst_pre.o:   ff.h
# # inst_pre.o:
# # inst_pre.o:
# # inst_pre.o:
# # inst_pre.o:
# # inst_pre.o:
# # inst_pre.o:
# # inst_pre.o:
# # inst_pre.o:
# # inst_pre.o:
# # inst_pre.o:
# # inst_pre.o:
# # inst_pre.o:
inst_pre.o:   output.h
inst_pre.o: memory.h expressions.h inst_pre.h#
inst_easy.o: ff.h #
# # inst_easy.o:
# # inst_easy.o:
# # inst_easy.o:
# # inst_easy.o:
# # inst_easy.o:
# # inst_easy.o:
# # inst_easy.o:
# # inst_easy.o:
# # inst_easy.o:
# # inst_easy.o:
# # inst_easy.o:
# # inst_easy.o:
# # inst_easy.o:
# inst_easy.o:   output.h
inst_easy.o: memory.h expressions.h inst_pre.h
inst_easy.o: inst_easy.h#
inst_hard.o: ff.h#
# # inst_hard.o:
# # inst_hard.o:
# # inst_hard.o:
# # inst_hard.o:
# # inst_hard.o:
# # inst_hard.o:
# # inst_hard.o:
# # inst_hard.o:
# # inst_hard.o:
# # inst_hard.o:
# # inst_hard.o:
# # inst_hard.o:
# # inst_hard.o:
# inst_hard.o:   output.h
inst_hard.o: memory.h expressions.h inst_pre.h
inst_hard.o: inst_hard.h#
# inst_final.o: ff.h #
# # inst_final.o:
# # inst_final.o:
# # inst_final.o:
# # inst_final.o:
# # inst_final.o:
# # inst_final.o:
# # inst_final.o:
# # inst_final.o:
# # inst_final.o:
# # inst_final.o:
# # inst_final.o:
# # inst_final.o:
# # inst_final.o:
inst_final.o:   output.h
inst_final.o: memory.h expressions.h inst_pre.h
inst_final.o: inst_final.h#
# relax.o: ff.h #
# # relax.o:
# # relax.o:
# # relax.o:
# # relax.o:
# # relax.o:
# # relax.o:
# # relax.o:
# # relax.o:
# # relax.o:
# # relax.o:
# # relax.o:
# # relax.o:
# # relax.o:
relax.o:  output.h memory.h
relax.o: expressions.h relax.h search.h#
search.o: ff.h ##
# # search.o:
# # search.o:
# # search.o:
# # search.o:
# # search.o:
# # search.o:
# # search.o:
# # search.o:
# # search.o:
# # search.o:
# # search.o:
# # search.o:
# # search.o:
search.o:   output.h memory.h
search.o:  expressions.h relax.h search.h
# # utility.o:
# # utility.o:
utility.o:   utility.h
utility.o: ff.h ##
# # utility.o:
# # utility.o:
# # utility.o:
# # utility.o:
# # utility.o:
# # utility.o:
# # utility.o:
# # utility.o:
# # utility.o:
# # utility.o:
# # utility.o:
utility.o: output.h
 test_main.o: libff.h ff.h #
# # test_main.o:
# # test_main.o:
# # test_main.o:
# # test_main.o:
# # test_main.o:
# # test_main.o:
# # test_main.o:
# # test_main.o:
# # test_main.o:
# # test_main.o:
# # test_main.o:
# # test_main.o:
# # test_main.o:
test_main.o:   output.h
