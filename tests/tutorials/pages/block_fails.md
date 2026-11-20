# A block that fails

```bash
echo first
```

```bash
echo "to stdout"
echo "something went wrong" >&2
false
echo "never reached"
```
