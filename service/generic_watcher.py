########################################################################################################################
# 
# Purpose: This class represents an observer, which accepts a list of injected processors. Each processor creates a handler 
# to watch for file system events in the specified folder. Each handler will call it's processor to process files as 
# they are created in the watched folder. The observer will start the handlers and run them in separate threads.
#
########################################################################################################################

from watchdog.observers import Observer  
from service.generic_handler import FileHandler
import time


#******************* LOAD THE CONFIGURATION FILE ********************************************
from dotenv import load_dotenv
load_dotenv()
#************************ CONFIGURATION ***********************************************************

class GenericWatcher:
  
    def __init__(self, processors):
        self.running = True
        self.observer = Observer()
        self.file_handlers = []
        self.processors = processors

    def start(self):

        # Create a handler instance for each folder to watch        
        for processor in self.processors:

            print(f"Watching folder: {processor.config['folder_to_watch']}")
                    
            image_handler =  FileHandler( processor)
            
            # Optionally, process all existing files in the folder tree:
            if processor.config['process_existing_files']:
                image_handler.ProcessALL()

            # schedule the handler to watch the folder
            self.file_handlers.append(image_handler)
            self.observer.schedule(image_handler, processor.config['folder_to_watch'], recursive=True)
                
        self.observer.start()

            
        
    def stop(self):

        self.running = False
        for image_handler in self.file_handlers:
            image_handler.stop()
           
        self.observer.stop()
        self.observer.join()

    def run(self):

        # go into an infinite loop.  The observer will run in a separate thread.
        try:
            while self.running:
                time.sleep(5)

        finally:
            self.stop()


       

