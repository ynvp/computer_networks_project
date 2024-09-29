# CSCE 5580 Section 002 - Computer Networks (Fall 2024 1)

## Group 8
1. Naga Vara Pradeep Yendluri
2. Venkata Varuna Sri Budidi
3. Jyothi Anjan Manini
4. Pradyumna Dyaga

## Installation instructions
1. Install virtualenv module to install all dependencies.
2. Use ``` pip install virtualenv ```
3. On windows create virtual environment using ``` virtualenv venv ```
4. Activate venv using ``` venv\Scripts\activate ```
5. Install dependencies using ``` pip install -r requirements.txt ```

## Starting server and spawning nodes
1. ``` python messaging_server.py <no_of_nodes> ``` example: ``` python messaging_server.py 2 ``` starts server and spawns 2 nodes.
2. All connected nodes are shown in server UI.
3. When a node is disconnected, server gracefully disconnects from node and closes socket associated with it.
4. When server shutdown button is clicked, it triggers all nodes to gracefully disconnect themselves from the socket and close the connections.
5. Connecting a node manually to server ``` python node.py <node_name> ``` example: ```python node.py "Node 4"```
6. Any connection to the server is updated in server UI.
![server screenshot with 2 nodes connected](image.png)
![alt text](image-1.png)

![1727581228062](image/README/1727581228062.png)
![1727581275789](image/README/1727581275789.png)