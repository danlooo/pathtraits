rm -rf etc/example
mkdir -p etc/example
cd etc/example

mkdir -p foo/bar
touch foo/bar/foo.txt
cat > foo/bar/foo.txt.yml <<'YAML'
mimetype: text/plain
size: 0
created: 2025-11-24T00:00:00Z
tags:
  - example
  - text
summary: "Placeholder metadata for foo.txt"
YAML

mkdir baz
touch baz/quox.png
cat > baz/quox.png.yml <<'YAML'
mimetype: image/png
dimensions:
  width: 800
  height: 600
created: 2025-11-24T00:00:00Z
tags:
  - example
  - image
YAML