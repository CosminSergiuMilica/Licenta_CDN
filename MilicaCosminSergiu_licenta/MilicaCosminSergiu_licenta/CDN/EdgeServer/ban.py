import uvicorn
from fastapi import FastAPI, Request, HTTPException, Response
from starlette.middleware.cors import CORSMiddleware
from module.baner import handle_ban_ip, store_blocked_ip, handle_unban_ip, remove_blocked_ip
from pymongo.errors import DuplicateKeyError
from utile.logging_conf import setup_logging
from utile.mongo_connection import connect_to_mongodb

app = FastAPI()
logger = setup_logging()
db, edge, client = connect_to_mongodb()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
@app.post("/ban")
async def ban_ip(request: Request):
    data = await request.json()
    try:
        ip_addresses = data.get("ip_addresses", [])
        logger.info(f"Received request at /ban endpoint with IP addresses: {ip_addresses}")
        for ip_address in ip_addresses:
            await handle_ban_ip(ip_address, db,logger)
        return {"message": "All IP addresses have been processed"}
    except DuplicateKeyError:
        logger.info(f"IP {ip_address} is already in the blocked_ips collection")
        raise HTTPException(status_code=409, detail="IP {ip_address} is already in the blocked_ips collection")
    except Exception as e:
        logger.error(f"Error in store_blocked_ip for IP {ip_address}: {e}")
        raise HTTPException(status_code=500, detail="Error in store_blocked_ip for IP {ip_address}:")
@app.post("/unban")
async def unban_ip(request: Request):
    try:
        data = await request.json()
        ip_addresses = data.get("ip_addresses", [])
        logger.info(f"Received request at /unban endpoint with IP addresses: {ip_addresses}")

        if not ip_addresses:
            raise HTTPException(status_code=400, detail="No IP addresses provided")

        for ip_address in ip_addresses:
            try:
                await handle_unban_ip(ip_address, logger)
                remove_blocked_ip(ip_address, db, logger)
            except Exception as e:
                logger.error(f"Error processing IP address {ip_address}: {e}")
                raise HTTPException(status_code=500, detail=f"Error processing IP address {ip_address}")
        return {"message": "All IP addresses have been processed"}
    except ValueError as e:
        logger.error(f"Invalid request data: {e}")
        raise HTTPException(status_code=400, detail="Invalid request data")

    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def main():
    uvicorn.run("ban:app", host="0.0.0.0", port=80, log_level="info", workers=3) # workers=15,


if __name__ == "__main__":
    main()