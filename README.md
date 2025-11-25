# pathtraits: Searchable Metadata DB of Files and Dirctories

## Get Started

```sh
python -m pip install 'pathtraits @ git+https://github.com/danlooo/pathtraits'
pathtraits start .

echo "test" > foo.txt
echo "test:true" > foo.txt.yml
```

## Developing

- normalize data base to store each new trait in a new table, allowing sparse traits