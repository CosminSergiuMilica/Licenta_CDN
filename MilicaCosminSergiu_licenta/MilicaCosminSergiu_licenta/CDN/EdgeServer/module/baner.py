import subprocess
from datetime import datetime

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError


async def handle_ban_ip(ip_address: str, db,logger):
    try:
        db.blocked_ips.insert_one({
            "ip_address": ip_address,
            "blocked_at": datetime.utcnow()
        })
        subprocess.run(['sudo', 'iptables', '-A', 'INPUT', '-s', ip_address, '-p', 'tcp', '--dport', '443', '-j', 'DROP'], check=True)
        logger.info(f"IP {ip_address} has been blocked.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to block IP {ip_address}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except DuplicateKeyError:
        logger.warning(f"IP {ip_address} is already blocked.")
        raise HTTPException(status_code=409, detail="IP address already blocked.")
    except Exception as e:
        logger.error(f"Failed to store IP {ip_address}: {e}")
        raise HTTPException(status_code=500, detail="Failed to store IP address.")

def store_blocked_ip(ip_address: str, db,logger):
#aici verifica daca a fost banat de altcineva
    try:
        db.blocked_ips.insert_one({
            "ip_address": ip_address,
            "blocked_at": datetime.utcnow()
        })
        logger.info(f"IP {ip_address} has been stored in the database.")
    except DuplicateKeyError:
        logger.warning(f"IP {ip_address} is already blocked.")
        raise HTTPException(status_code=409, detail="IP address already blocked.")
    except Exception as e:
        logger.error(f"Failed to store IP {ip_address}: {e}")
        raise HTTPException(status_code=500, detail="Failed to store IP address.")

async def handle_unban_ip(ip_address: str, logger):
    try:
        while True:
            check_rule = subprocess.run(
                ['sudo', 'iptables', '-C', 'INPUT', '-s', ip_address, '-p', 'tcp', '--dport', '443', '-j', 'DROP'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            if check_rule.returncode == 0:
                remove_rule = subprocess.run(
                    ['sudo', 'iptables', '-D', 'INPUT', '-s', ip_address, '-p', 'tcp', '--dport', '443', '-j', 'DROP'],
                    check=True
                )
                if remove_rule.returncode == 0:
                    logger.info(f"IP {ip_address} has been unblocked.")
                else:
                    logger.error(f"Failed to remove blocking rule for IP {ip_address}.")
                    raise HTTPException(status_code=500, detail=f"Failed to remove blocking rule for IP {ip_address}.")
            else:
                logger.warning(f"No more blocking rules found for IP {ip_address}.")
                return {"message": f"IP {ip_address} has been unblocked from all rules."}
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to unblock IP {ip_address}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unblock IP")

def remove_blocked_ip(ip_address: str, db, logger):
    try:
        result = db.blocked_ips.delete_one({"ip_address": ip_address})
        if result.deleted_count > 0:
            logger.info(f"IP {ip_address} has been removed from the database.")
        else:
            logger.warning(f"IP {ip_address} not found in the database.")
    except Exception as e:
        logger.error(f"Failed to deleted IP {ip_address} {e}")
        raise HTTPException(status_code=500, detail=f"Failed to deleted IP")