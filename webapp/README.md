# About
This application serves as the **frontend** of ProxyAlly.

# Prerequisites
Following are the required environments needed to successfully run this application 
+ **Python** 3.7.5 along with a latest version of **pip** installed
+ **Backend (webapi)** is running properly

# How to run
Navigate to **webapp** directory from command prompt and perform the following steps:

1. Resolve python dependencies. A virtual environment is always better to consider       
   ```
   pip install -r requirements.txt
   ```
    
2. Set Environment Variables (OS dependant). You can **skip** this step and stay with the default values as below
    ```
    SERVER_HOST=localhost
    SERVER_PORT=5000
    API_ROOT=http://localhost:5001/api/v1
    ```

3. Run. (info: for linux it the command can be **python3**)
    ```
    python runserver.py
    ```
    
4. Open up your favourite API tester and Open up your favourite browser and hit `http://localhost:5000`


## Quick run
Navigate to **webapi** and **webapp** directory consequently and execute `run.bat` (Windows) or `run.sh` (Unix like OS)

*Note-1: You may need to resolve permission requirements to execute files depending on Operation System*

*Note-2: All the environment variables will remain set with default values*

