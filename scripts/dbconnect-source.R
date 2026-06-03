# ===========================================================================
# DEPRECATED: Do not store credentials in code. Use .env and the FastMCP
# server instead. See docs/README.md for setup instructions.
# This file is kept for historical reference only.
# ===========================================================================

# Loading libraries -------------------------------------------------------

## Install necessary packages, then execute:

library(dplyr)
library(RMySQL)
library(odbc)
library(tidyverse)

# Establish connection to server db ---------------------------------------

## Connection details

# Important: Do not modify
# Requires user and password manual input
""
host="ecological-monitoring.cqv0gwa2gczv.us-east-1.rds.amazonaws.com"
user= "mcp_ltem_ro"
dbname= "ecological_monitoring"
password= "!4)nAy5ED4!(y-N3"




# This connects to the database (creates an image, does not actually download anything)
ltem_db_ro  = dbConnect(MySQL(),
                    dbname=dbname,
                    host=host,
                    user= user,
                    password= password)



