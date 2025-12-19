# pathtraits: Annotate files and directories

Create a YAML file "meta.yml" inside a directory to annotate all files in that directory with any attributes.
The data will be collected in a SQLite database to query and visualize.

## Get Started

```sh
# install
python -m pip install pathtraits

# create some test data
echo "test" > foo.txt
echo "test: true" > foo.txt.yml

# create database
pathtraits batch .

# query traits
pathtraits get foo.txt
```

## Developing

- use Pylint 
- normalize data base to 3NF to store each new trait in a new table, allowing sparse traits
