import os
import shutil
import time
import argparse
import logging

class DirectoryStateUpdater:
    def __init__(self, directory_path):
        self.directory_path = directory_path

    def update_state(self):
        state = {}
        for root, dirs, files in os.walk(self.directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                state[file_path] = os.path.getmtime(file_path)
        return state

class FileSynchronizer:
    def __init__(self, source_state, replica_state, source_directory, replica_directory):
        self.source_state = source_state
        self.replica_state = replica_state
        self.source_directory = source_directory
        self.replica_directory = replica_directory

    def synchronize(self):
        for file_path, timestamp in self.source_state.items():
            replica_file = os.path.join(self.replica_directory, os.path.relpath(file_path, self.source_directory))
            try:
                if replica_file not in self.replica_state or self.replica_state[replica_file] < timestamp:
                    shutil.copy2(file_path, replica_file)
                    logging.info(f"File synchronized: {file_path} -> {replica_file}")
            except Exception as e:
                logging.error(f"Failed to synchronize file: {file_path} -> {replica_file} - {e}")

        for file_path in self.replica_state.keys():
            source_file = os.path.join(self.source_directory, os.path.relpath(file_path, self.replica_directory))
            if source_file not in self.source_state:
                try:
                    os.remove(file_path)
                    logging.info(f"File removed from replica: {file_path}")
                except Exception as e:
                    logging.error(f"Failed to remove file from replica: {file_path} - {e}")

class DirectorySynchronizer:
    def __init__(self, source_directory, replica_directory):
        self.source_directory = source_directory
        self.replica_directory = replica_directory

    def synchronize(self):
        source_updater = DirectoryStateUpdater(self.source_directory)
        replica_updater = DirectoryStateUpdater(self.replica_directory)
        source_state = source_updater.update_state()
        replica_state = replica_updater.update_state()
        
        synchronizer = FileSynchronizer(source_state, replica_state, self.source_directory, self.replica_directory)
        synchronizer.synchronize()

class FolderSynchronizationDaemon:
    def __init__(self, source_directory, replica_directory, sync_interval, log_file):
        self.source_directory = source_directory
        self.replica_directory = replica_directory
        self.sync_interval = sync_interval
        self.log_file = log_file

        os.makedirs(source_directory, exist_ok=True)
        os.makedirs(replica_directory, exist_ok=True)

    def run(self):
        logging.basicConfig(filename=self.log_file, level=logging.INFO, format="%(asctime)s - %(message)s")
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        console.setFormatter(formatter)
        logging.getLogger().addHandler(console)

        while True:
            synchronizer = DirectorySynchronizer(self.source_directory, self.replica_directory)
            synchronizer.synchronize()
            time.sleep(self.sync_interval)

def main():
    parser = argparse.ArgumentParser(description="Directory synchronization program")
    parser.add_argument("source_directory", help="Path to the source directory")
    parser.add_argument("replica_directory", help="Path to the replica directory")
    parser.add_argument("sync_interval", type=int, help="Synchronization interval in seconds")
    parser.add_argument("log_file", help="Path to the log file")
    args = parser.parse_args()

    log_dir = os.path.dirname(args.log_file)
    os.makedirs(log_dir, exist_ok=True)

    daemon = FolderSynchronizationDaemon(args.source_directory, args.replica_directory, args.sync_interval, args.log_file)
    daemon.run()

if __name__ == "__main__":
    main()
