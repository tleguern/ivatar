for size in $(seq 1 512); do
    inkscape -z -e ivatar/static/img/nobody/${size}.png -w ${size} -h ${size} \
      ivatar/static/img/libravatar_logo.svg
done
