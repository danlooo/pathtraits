# pathtraits: Annotate files and directories

Create a YAML file "meta.yml" inside a directory to annotate all files in that directory with any attributes.
The data will be collected in a SQLite database to query and visualize.

## Get Started

```sh
python -m pip install 'pathtraits @ git+https://github.com/danlooo/pathtraits'
pathtraits watch .

echo "test" > foo.txt
echo "test:true" > foo.txt.yml
```

## Developing

- normalize data base to store each new trait in a new table, allowing sparse traits
