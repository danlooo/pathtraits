# pathtraits: Annotate files and directories

Create a YAML file "meta.yml" inside a directory to annotate all files in that directory with any attributes.
The data will be collected in a SQLite database to query and visualize.

## Get Started

Pathtraits are attributes of files and directories stores in YAML side car files.
Pathtraits of parent directories are inherited for a given path and can be overwritten by those of child directories.
Pathtraits can be either of type string, int, or real.


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

## Configuration

### Database path

The databse is being created in your home directory by default at "~/.pathtraits.db".
One can change this by setting the environmental variable `PATHTRAITS_DB_PATH` to any other path with write permssions if needed.

## Developing

- use Pylint 
- normalize data base to 3NF to store each new trait in a new table, allowing sparse traits
