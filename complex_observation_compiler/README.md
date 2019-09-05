

    Jennifer Nelson
    Complex Observations for Plan Recognition as Planning: A Compiler
    Copyright (C) 2019

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

This software is adapted from work by Miguel Ramirez, Nir Lipovetzky, Hector Geffner, under the GNU General Public License. See https://sites.google.com/site/prasplanning/file-cabinet (obs-compiler.tar.bz2) for an original copy.
#### Changes:
- Addition of this README
- Addition of all files with '_complex' suffix.
- Changes to main, string_ops and Makefile
- Change to usage() in options.cxx
- Numerous small changes elsewhere to solve compilation issues




### Dependencies:
- bison 2.3 +
- flex 2.5.33 +

(Make sure the Makefile has the correct command to call these.)
To check if you have these, use
```
which bison
which flex
```
If missing, macs can use brew ([brew.sh](https://brew.sh)) to install:
```
brew install bison
brew install flex
```

### Compiling
This uses a modified version of metric-ff to parse PDDL and ground it, so that needs to be compiled first.

```
cd mod-metric-ff
make libff
cd ..
make
```

### Usage:
```
pr2plan_complex -d <domain file> -i <instance file> -o <observation file>"
```
##### Optional parameters:
- -v         Verbose Mode ON (default is OFF)
- -F         Introduce forgo(obs) ops
- -P         Generate Planning problems necessary for probabilistic PR
