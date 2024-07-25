from datetime import datetime

TIMESTAMP_YEAR = 31536000
MONERO_LAUNCH_YEAR = TIMESTAMP_YEAR*44-3600+3600*24*11


def init_cst_distribution():
    res = []
    biss = 0
    cpt = 1
    for i in range(0, 13):
        if cpt == 4:
            biss+=3600*24
            cpt = 0
        res.append(MONERO_LAUNCH_YEAR+ (i*TIMESTAMP_YEAR)+biss)    
        cpt+=1
    return res

DISTRIBUTION_YEAR = init_cst_distribution()    
#DISTRIBUTION_MONTH = init_cst_distribution()


def timestamp_to_date(timestamp:int):
    return datetime.fromtimestamp(timestamp)    