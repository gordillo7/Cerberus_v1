"""Usar Feroxbuster para realizar el modulo de fuzzing web
    # Ponerle un timeout, por ejemplo 5 minutos y si el escaneo
    tarda mas de esos 5 minutos, cortarlo y quedarnos con los resultados
    hasta ese momento.
    # Controlar http y https mediante http_detect_scheme.py, ya que feroxbuster
    asigna https por defecto si se le pasa el target sin schema (revisar el modulo
    http_detect_scheme.py ya que creo que no funciona correctamente)"""