import comtypes.client
import os
import sys
import time

def init_powerpoint():
    powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
    powerpoint.Visible = 1
    return powerpoint
 
def ppt_to_pdf(powerpoint, inputFileName, outputFileName, formatType = 32):
    if outputFileName[-3:] != 'pdf':
        outputFileName = outputFileName.replace(".pptx","").replace(".ppt","").replace("GENERATED_PPTX","GENERATED_PDF") + ".pdf"
    deck = powerpoint.Presentations.Open(inputFileName)
    deck.SaveAs(outputFileName, formatType) # formatType = 32 for ppt to pdf
    deck.Close()
    print('convert %s file complete '%outputFileName)
 
def convert_files_in_folder(powerpoint, folder):
    print(folder)
    #time.sleep(10)
    ppt_to_pdf(powerpoint, folder, folder)
 
if __name__ == "__main__":
    file = sys.argv[1]
    now = sys.argv[2]
    print(sys.argv)
    file = file.replace("©", " ")
    print(file)
    #time.sleep(10)
    powerpoint = init_powerpoint()
    cwd = os.getcwd() + "\GENERATED_PPTX\\"+ now +"\\"+ file + ".pptx"
    print("cwd = ", cwd)
    convert_files_in_folder(powerpoint, cwd)
    powerpoint.Quit()