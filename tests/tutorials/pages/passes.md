# A page that passes

<!-- tutorial: requires bash -->

Files, variables, functions and the directory carry from block to block.

```bash
mkdir -p work && cd work
GREETING="hello"
shout() { echo "${1^^}"; }
printf 'gene,a,b\ng1,1,2\n' > counts.csv
```

```bash
echo "$GREETING from $(basename "$PWD")"
shout "$GREETING"
```

<!-- tutorial: expect -->
```text
hello from work
HELLO
```

Exported variables carry too, and changes to existing ones such as `PATH`.

```bash
export PATH="$PWD/bin:$PATH"
mkdir -p bin && printf '#!/bin/sh\necho local tool\n' > bin/tool && chmod +x bin/tool
```

```bash
tool
wc -l < counts.csv
```

<!-- tutorial: expect -->
```text
local tool
2
```

`...` stands for text that varies:

```bash
echo "run took 1.2345 seconds on $(date +%F)"
```

<!-- tutorial: expect -->
```text
run took 1.23... seconds on ...
```

A pattern, for exactness of form without the value:

```bash
echo "p = 0.0412"
```

<!-- tutorial: expect regex -->
```text
p = 0\.0\d+
```

A check that must fail; the output shown is its stderr.

<!-- tutorial: fails -->
```bash
echo "bad value" >&2
exit 3
```

<!-- tutorial: expect -->
```text
bad value
```

detk is on PATH:

```bash
detk-stats --help | head -n 1 > help.txt
test -s help.txt
```

<!-- tutorial: hidden
```bash
test -f counts.csv
echo "hidden ran" > hidden.txt
```
-->

Blocks in other languages are shown but not run:

```console
$ this would fail if it ran
```

```python
raise SystemExit(1)
```
