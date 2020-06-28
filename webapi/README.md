# About
This application serves as the **backend** of ProxyAlly. It provides all the services through REST interfaces.

# Prerequisites
Following are the required environments needed to successfully run this application 
+ **Python** 3.7.5 along with a latest version of **pip** installed
+ **MongoDB** 4.2.7 Community

# How to run
Navigate to **webapi** directory from command prompt and perform the following steps:

1. Resolve python dependencies. A virtual environment is always better to consider       
   ```
   pip install -r requirements.txt
   ```
    
2. Set Environment Variables (OS dependant). You can **skip** this step and stay with the default values as below
     ```
    SERVER_HOST=localhost
    SERVER_PORT=5001
    MONGO_URI=mongodb://localhost:27017/proxyAllyDB
     ```
    *Note: The database will be created and initialized based on MONGO_URI. If you change this URI later the previous database remains untouched*

3. Run. (info: for linux it the command can be **python3**)
    ```
    python runserver.py
    ```
    
4. Open up your favourite API tester and start with `http://localhost:5001/{endpoint}/{params}`
See the API documentation for more details.


## Quick run
Navigate to **webapi** and **webapp** directory consequently and execute `run.bat` (Windows) or `run.sh` (Unix like OS)

*Note-1: You may need to resolve permission requirements to execute files depending on Operation System*

*Note-2: All the environment variables will remain set with default values*

# Special Remark
in `config.py` if `DEBUG=TRUE` then the application will fetch proxies from offline files saved in `/core/proxy_fetchers/providers_offline/` 