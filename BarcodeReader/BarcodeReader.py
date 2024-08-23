import cv2
from pyzbar import pyzbar
import winsound
import pandas as pd
from argparse import ArgumentParser
from time import time

def create_requirementstxt():
    import os
    import numpy
    import pyzbar as pz
    
    curdir=os.path.dirname(os.path.realpath(__file__))
    print(curdir)
    
    numpy_version=f"numpy=={numpy.__version__}"
    opencv_version=f"opencv=={cv2.__version__}"
    pyzbar_version=f"pyzbar=={pz.__version__}"
    pandas_version=f"pandas=={pd.__version__}"
    print(numpy_version)
    print(opencv_version)
    print(pyzbar_version)
    print(pandas_version)
    
    versions = [
        numpy_version,
        opencv_version,
        pyzbar_version,
        pandas_version,
    ]
    
    with open(os.path.join(curdir, "requirements.txt"), "w") as f:
        f.writelines('\n'.join(versions) + '\n')

def detect(database: pd.DataFrame, rescan_interval:int):
    frequency = 2500  # Set Frequency To 2500 Hertz
    duration = 100  # Set Duration To 1000 ms == 1 second
    cap = cv2.VideoCapture(0)

    prev_barcodes = dict()
    while True:
        ret, frame = cap.read()
        
        prev_barcodes = {key: prev_barcodes[key] for key in prev_barcodes.keys() if (time() - prev_barcodes[key]) < rescan_interval}
        
        if frame is not None:
            barcodes = pyzbar.decode(frame)
            if len(barcodes):
                for barcode in barcodes:
                    (x, y, w, h) = barcode.rect
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    
                    barcodeData = barcode.data.decode("utf-8")
                    barcodeType = barcode.type
                    
                    text = "{} ({})".format(barcodeData, barcodeType)
                    cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    print("[INFO] Found {} barcode: {}".format(barcodeType, barcodeData))
                    
                    if int(barcodeData) in database["codes"].tolist():
                        if barcodeData not in prev_barcodes.keys():
                            print(database.loc[database['codes'] == int(barcodeData)])
                            winsound.Beep(frequency, duration)  
                            prev_barcodes[barcodeData] = time()
                                 
            cv2.imshow("frame", frame)
        if cv2.waitKey(1) == ord("q"):
            break
        
    cv2.destroyAllWindows()
    

def get_database(args):
    df = pd.read_csv(args.database_path, sep=",")
    return df
    
    
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--database-path", type=str, help="path to CSV file containing barcodes and descriptions")
    parser.add_argument("--rescan-interval", type=int, default=2, help="wait time (seconds) to rescan the same product")
    args = parser.parse_args()
    
    database = get_database(args)
    detect(database, args.rescan_interval)
    # create_requirementstxt()