#!/usr/bin/env bash
#
# Package built addons into release assets.
#
# For each tier, produces dist/DESI_DR1_<tier>.zip containing:
#
#     DESI_DR1_<tier>/
#       DESI_DR1_<tier>.pak      catalogs/ at the archive root
#       README.md                readable without unpacking anything
#       CITATIONS.txt            ditto - CC BY 4.0 attribution
#
# The .pak layout is not arbitrary. Per the SpaceEngine manual
# (https://spaceengine.org/manual/making-addons/):
#
#     "The pak file cannot contain additional subfolders, only default
#      ones are allowed."
#
# The topmost entries inside a .pak must be standard SE folders --
# catalogs, models, textures. Zipping the DESI_DR1_<tier> directory
# itself would put a non-standard folder at the archive root and SE
# would not load it. So the .pak is built from *inside* the addon
# directory, and only from catalogs/.
#
# Usage:
#     ./package_release.sh                # all four tiers
#     ./package_release.sh lite heavy     # named tiers only
#
set -euo pipefail

cd "$(dirname "$0")"

ADDONS_DIR=addons
DIST_DIR=dist
TIERS=("${@:-}")
if [ -z "${TIERS[0]}" ]; then
    TIERS=(lite normal heavy insane)
fi

command -v zip >/dev/null || { echo "error: 'zip' not installed" >&2; exit 1; }

mkdir -p "$DIST_DIR"

for tier in "${TIERS[@]}"; do
    name="DESI_DR1_${tier}"
    src="$ADDONS_DIR/$name"

    if [ ! -d "$src/catalogs" ]; then
        echo "skip $tier: no $src/catalogs (build it first with convert.py)" >&2
        continue
    fi

    echo "==> $name"

    staging="$DIST_DIR/.staging/$name"
    rm -rf "$DIST_DIR/.staging"
    mkdir -p "$staging"

    # 1. The .pak: catalogs/ at the archive root, nothing above it.
    #    -9 because these ship once and download many times.
    #    Kept in dist/ as a standalone asset - a .pak dropped straight
    #    into addons/ is a valid install with no unzip step.
    rm -f "$DIST_DIR/$name.pak"
    ( cd "$src" && zip -q -r -9 "$OLDPWD/$DIST_DIR/$name.pak" catalogs )

    # 2. Also assemble the folder form, which carries the docs. Hardlink
    #    the pak rather than copying - these run to hundreds of MB.
    ln "$DIST_DIR/$name.pak" "$staging/$name.pak"
    cp "$src/README.md" "$src/CITATIONS.txt" "$staging/"

    # 3. Outer zip. -0 (store): the .pak is already compressed, so
    #    recompressing it wastes minutes and saves nothing.
    ( cd "$DIST_DIR/.staging" && zip -q -r -0 "$OLDPWD/$DIST_DIR/$name.zip" "$name" )

    rm -rf "$DIST_DIR/.staging"

    echo "    $DIST_DIR/$name.pak  ($(du -h "$DIST_DIR/$name.pak" | cut -f1))"
    echo "    $DIST_DIR/$name.zip  ($(du -h "$DIST_DIR/$name.zip" | cut -f1))"
done

echo
echo "Verifying .pak roots (must contain only standard SE folders):"
for tier in "${TIERS[@]}"; do
    name="DESI_DR1_${tier}"
    pak="$DIST_DIR/$name.pak"
    [ -f "$pak" ] || continue
    roots=$(unzip -Z1 "$pak" | cut -d/ -f1 | sort -u | tr '\n' ' ')
    case "$roots" in
        "catalogs ") echo "    $name.pak: OK ($roots)" ;;
        *)           echo "    $name.pak: BAD ROOT -> $roots" >&2; exit 1 ;;
    esac
done

echo
echo "Release assets ready in $DIST_DIR/"
