import json
import networkx as nx
import os
import sys
import argparse
import time
from datetime import datetime
import bz2

def get_tweets(path, fecha_inicial, fecha_final, hashtags):
    tweets = []

    for year_folder in os.listdir(path):
        year_path = os.path.join(path, year_folder)
        year = int(year_folder)
        pass1 = 1
        lower = 0
        upper = 0
        if fecha_inicial.year <= year <= fecha_final.year:
            if (fecha_inicial.year == year or fecha_final.year == year):
                pass1 = 0
                if fecha_inicial.year == year:
                    lower = 1
                if fecha_final.year == year:
                    upper = 1
            for month_folder in os.listdir(year_path):
                month_path = os.path.join(year_path, month_folder)
                month = int(month_folder)
                if ((fecha_inicial.month <= month and lower ==1) or (month <= fecha_final.month and upper == 1) | pass1==1):
                    if (fecha_inicial.month == month or fecha_final.month == month):
                        if fecha_inicial.month == month:
                            lower = 1
                        else:
                            lower = 0
                        if fecha_final.month == month:
                            upper = 1
                        else:
                            upper = 0
                    else:
                        pass1 = 1
                        upper = 0
                        lower = 0
                    for day_folder in os.listdir(month_path):
                        day_path = os.path.join(month_path, day_folder)
                        day = int(day_folder)
                        if ((fecha_inicial.day <= day and lower ==1) or (day <= fecha_final.day and upper == 1) or pass1==1):
                            for root, dirs, files in os.walk(day_path):
                                for file in files:
                                        if file.endswith(".json.bz2"):
                                                file_path = os.path.join(root, file)
                                                with bz2.BZ2File(file_path, "r") as f: #r
                                                    try:
                                                        for line in f:
                                                            if line.strip():
                                                                tweet = json.loads(line)
                                                                if "created_at" in tweet:
                                                                    if hashtags:
                                                                        if tweet["entities"]["hashtags"]:
                                                                            hashtexts = [hashtag["text"] for hashtag in tweet["entities"]["hashtags"]]
                                                                            added = 0
                                                                            if (any(item in hashtexts for item in hashtags) and added==0): #Para que no se guarde varias veces el mismo tweet
                                                                                tweets.append(tweet)
                                                                                added = 1
                                                                    else:
                                                                        tweets.append(tweet)
                                                    except UnicodeDecodeError:
                                                        print(f"Error de codificación en el archivo: {file_path}")
                                                    except json.decoder.JSONDecodeError as e:
                                                        print(f"Error de JSON en el archivo: {file_path}")
                                                        print(e)
    return tweets

# Crear los grafos y JSON

def crear_grafo_retweets(tweets):
    grafo = nx.DiGraph()  # Utilizamos un grafo dirigido para representar retweets

    for tweet in tweets:
        if 'user' in tweet:
            user_screen_name = tweet["user"]["screen_name"]
            tweet_id = tweet["id_str"]
            tweet_text = tweet["text"]

            if tweet_id not in grafo:
                grafo.add_node(user_screen_name) 

            if "retweeted_status" in tweet:
                original_tweet = tweet["retweeted_status"]
                original_user_screen_name = original_tweet["user"]["screen_name"]
                original_tweet_id = original_tweet["id_str"]
                if original_tweet_id not in grafo:
                    grafo.add_node(original_user_screen_name) 
                # Comprobamos si la arista ya existe entre estos usuarios
                if grafo.has_edge(user_screen_name, original_user_screen_name):
                    grafo[user_screen_name][original_user_screen_name]["weight"] += 1
                else:
                    grafo.add_edge(user_screen_name, original_user_screen_name, weight=1)

    return grafo


def crear_json_retweets(tweets):
    result = {}

    for tweet in tweets:
        if 'user' in tweet:
            user_screen_name = tweet["user"]["screen_name"]

            if "retweeted_status" in tweet:
                original_tweet = tweet["retweeted_status"]
                original_user_screen_name = "user: " + original_tweet["user"]["screen_name"]

                if original_user_screen_name not in result:
                    result[original_user_screen_name] = {
                        "received retweets": 0,
                        "tweets": {}
                    }

                original_tweet_id = "tweet id: " + original_tweet["id_str"]

                if original_tweet_id not in result[original_user_screen_name]["tweets"]:
                    result[original_user_screen_name]["tweets"][original_tweet_id] = {
                        "retweeted by": []
                    }
                if user_screen_name not in result[original_user_screen_name]["tweets"][original_tweet_id]["retweeted by"]:
                    result[original_user_screen_name]["tweets"][original_tweet_id]["retweeted by"].append(user_screen_name)
                    result[original_user_screen_name]["received retweets"] += 1

    # Ordenar el JSON por número total de retweets de mayor a menor
    sorted_result = dict(sorted(result.items(), key=lambda x: x[1]["received retweets"], reverse=True))
    return sorted_result



def crear_json_menciones(tweets):
    result = {}

    for tweet in tweets:
        if 'user' in tweet:
          if "retweeted_status" not in tweet:  # Verificar que no sea un retweet
                user_screen_name = tweet["user"]["screen_name"]
                mentioned_users = [mencion["screen_name"] for mencion in tweet.get("entities", {}).get("user_mentions", [])]
                repeats = {}
                for mentioned_user in mentioned_users:
                  mentioned_user = "user: " + mentioned_user
                  if mentioned_user not in repeats: 
                    repeats[mentioned_user] = 1
                    if mentioned_user not in result:
                        result[mentioned_user] = {
                        "received mentions": 0,
                        "mentions": {}
                    }
                    if user_screen_name not in result[mentioned_user]['mentions']:
                        result[mentioned_user]['mentions'][user_screen_name] = {
                            "mention by": user_screen_name,
                            "tweets": []
                        }
                        result[mentioned_user]["mentions"][user_screen_name]["tweets"].append(tweet["id_str"])
                    else:
                        result[mentioned_user]["mentions"][user_screen_name]["tweets"].append(tweet["id_str"])
                    result[mentioned_user]["received mentions"] += 1

    # Ordenar el JSON por número de menciones de mayor a menor
    sorted_result = dict(sorted(result.items(), key=lambda x: x[1]["received mentions"], reverse=True))
    return sorted_result

def crear_grafo_menciones(tweets):
    grafo = nx.DiGraph() 

    for tweet in tweets:
        if 'user' in tweet:
          if "retweeted_status" not in tweet:  # Verificar que no sea un retweet
            user_screen_name = tweet["user"]["screen_name"]
            tweet_id = tweet["id_str"]
            tweet_text = tweet["text"]

            mentioned_users = [mencion["screen_name"] for mencion in tweet.get("entities", {}).get("user_mentions", [])]
            repeats = {}
            if user_screen_name not in grafo:
                grafo.add_node(user_screen_name)

            for mentioned_user in mentioned_users:
              if mentioned_user not in repeats: 
                repeats[mentioned_user] = 1
                if mentioned_user not in grafo:
                    grafo.add_node(mentioned_user)

                # Comprobamos si la arista ya existe entre estos usuarios
                if grafo.has_edge(user_screen_name, mentioned_user):
                    grafo[user_screen_name][mentioned_user]["weight"] += 1
                else:
                    grafo.add_edge(user_screen_name, mentioned_user, weight=1)

    return grafo


def crear_json_coretweets(tweets):
    retweet_dict = {} 
    for tweet in tweets:
        retweeter = tweet['user']['screen_name']

        # Comprobar si el tweet es un retweet
        if 'retweeted_status' in tweet and 'user' in tweet:
          author = tweet['retweeted_status']['user']['screen_name']
          if author != retweeter:
            # Actualizar el diccionario de retweets
            if retweeter not in retweet_dict and author:
                retweet_dict[retweeter] = []
            retweet_dict[retweeter].append(author) 
    result = {}  
    for clave, lista in retweet_dict.items():
        elementos_vistos = []
        for elemento in lista:
            if elemento not in elementos_vistos:
                if elemento != clave:
                    elementos_vistos.append(elemento)
        # Almacenar el par en el diccionario de pares iguales
        combinaciones = combinations(elementos_vistos, 2)
        for combo in combinaciones:
            parautores = f"authors: {[combo[0], combo[1]]}"
            parautores2 = f"authors: {[combo[1], combo[0]]}"
            if parautores not in result and parautores2 not in result:
                result[parautores] = {
                    'total coretweets': 0,
                    'retweeters': [] 
                }
                result[parautores]['retweeters'].append(clave)
                result[parautores]['total coretweets'] += 1
            elif parautores in result and parautores2 not in result:
                if clave not in result[parautores]['retweeters']:
                    result[parautores]['retweeters'].append(clave)
                    result[parautores]['total coretweets'] += 1
    sorted_result = dict(sorted(result.items(), key=lambda x: x[1]["total coretweets"], reverse=True))
    return sorted_result

def crear_grafo_coretweets(tweets):
    grafo = nx.Graph() 
    retweet_dict = {}  
    for tweet in tweets:
        retweeter = tweet['user']['screen_name']  

        # Comprobar si el tweet es un retweet
        if 'retweeted_status' in tweet and 'user' in tweet:
          author = tweet['retweeted_status']['user']['screen_name']
          og_tweet = tweet['retweeted_status']['text']
          if author != retweeter:
            if author not in retweet_dict:
                retweet_dict[author] = []
            retweet_dict[author].append((og_tweet, retweeter))
    # Encontrar pares de tweets retuiteados por el mismo usuario
    result = {}  
    for clave1, tuplas1 in retweet_dict.items():
        for clave2, tuplas2 in retweet_dict.items():
            if clave1 != clave2:
                for tupla1 in tuplas1:
                    for tupla2 in tuplas2:
                        if tupla1[1] == tupla2[1] and tupla1[1] != clave2 and tupla2[1] != clave1:
                            if clave1 not in grafo:
                                grafo.add_node(clave1)
                            if clave2 not in grafo:
                                grafo.add_node(clave2)  
                            parautores = f"tweet authors: {clave1} and {clave2}"
                            parautores2 = f"tweet authors: {clave2} and {clave1}"
                            if parautores not in result and parautores2 not in result:
                                if grafo.has_edge(clave1, clave2): #En teoria no se deberia dar nunca pero por si acaso
                                    grafo[clave1][clave2]["weight"] += 1
                                else: 
                                    grafo.add_edge(clave1, clave2, weight=1)
                                result[parautores] = {
                                    'retweeters': [] 
                                }
                                result[parautores]['retweeters'].append(tupla1[1])
                            elif parautores in result and parautores2 not in result:
                                 if tupla1[1] not in result[parautores]['retweeters']:
                                    result[parautores]['retweeters'].append(tupla1[1])
                                    if grafo.has_edge(clave1, clave2): 
                                        grafo[clave1][clave2]["weight"] += 1
                                    else: 
                                        grafo.add_edge(clave1, clave2, weight=1)

    return grafo



def imprimir_resultados(grafo, salida):
    if salida.endswith(".gexf"):
        nx.write_gexf(grafo, salida)
    elif salida.endswith(".json"):
        with open(salida, "w") as f:
            json.dump(list(grafo.nodes(data=True)), f, indent=4) 

def parse_args(argv):
    parser = argparse.ArgumentParser(description="Argumentos para generador.py", add_help=False)
    parser.add_argument("-d", "--directory", default="data", help="Ruta al directorio de datos")
    parser.add_argument("-fi", "--fecha-inicial", help="Fecha inicial")
    parser.add_argument("-ff", "--fecha-final", help="Fecha final")
    parser.add_argument("-h", "--hashtags", help="Lista de hashtags")
    parser.add_argument("-grt", action="store_true", help="Crear grafo de retweets")
    parser.add_argument("-jrt", action="store_true", help="Crear JSON de retweets")
    parser.add_argument("-gm", action="store_true", help="Crear grafo de menciones")
    parser.add_argument("-jm", action="store_true", help="Crear JSON de menciones")
    parser.add_argument("-gcrt", action="store_true", help="Crear grafo de corretweets")
    parser.add_argument("-jcrt", action="store_true", help="Crear JSON de corretweets")
    args = parser.parse_args(argv)
    args = vars(args)
    if "directory" not in args:
       args["directory"] = "data"
    return args

def main():
    args = parse_args(sys.argv[1:])
    
    fecha_inicial = datetime.strptime("01-01-1990", "%d-%m-%Y")
    fecha_final =   datetime.strptime("01-01-2024", "%d-%m-%Y")

    if args["fecha_inicial"]:
        fecha_inicial = datetime.strptime(args["fecha_inicial"], "%d-%m-%Y")

    if args["fecha_final"]:
        fecha_final = datetime.strptime(args["fecha_final"], "%d-%m-%Y")

    hashtagsl = []
    if args["hashtags"]:
        current_directory = os.getcwd()
        route = os.path.join(current_directory, args["hashtags"])
        with open(route, 'r') as archivo:
            hashtagsl = [line.strip() for line in archivo.readlines()]
        for index in range (0,len(hashtagsl)):
            word = hashtagsl[index]
            if word.startswith("#"):
                hashtagsl[index] = word[1:]

    tweets = get_tweets(args["directory"], fecha_inicial, fecha_final, hashtagsl)

    if args["grt"]:
        grafo = crear_grafo_retweets(tweets)
        imprimir_resultados(grafo, "rt.gexf")
    if args["jrt"]:
        json_retweets = crear_json_retweets(tweets)
        with open("rt.json", "w") as f:
            json.dump(json_retweets, f, indent=4)  
    if args["gm"]:
        grafo = crear_grafo_menciones(tweets)
        imprimir_resultados(grafo, "mención.gexf")
    if args["jm"]: 
        json_menciones = crear_json_menciones(tweets)
        with open("mención.json", "w") as f:
            json.dump(json_menciones, f, indent=4)
    if args["gcrt"]:
        grafo = crear_grafo_coretweets(tweets)
        imprimir_resultados(grafo, "corrtw.gexf")
    if args["jcrt"]:
        json_corretweets = crear_json_coretweets(tweets)
        with open("corrtw.json", "w") as f:
           json.dump(json_corretweets, f, indent=4)

    print(time.time() - start_time)

if __name__ == "__main__":
    start_time = time.time()
    main()
