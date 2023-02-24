import os
import sys

import uvicorn
import app

if __name__ == "__main__":
    port = 5000
    host = '0.0.0.0'
    uvicorn.run(app.fast_api, host=host, port=port, workers=1)
