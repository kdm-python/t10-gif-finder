SELECT * FROM gifs
INNER JOIN tags ON gifs.id = tags.gif_id
WHERE author = 'martinstr'
AND tags.tag IN ('licka', 'sussy', 'muzz')
AND stream_id = '3';