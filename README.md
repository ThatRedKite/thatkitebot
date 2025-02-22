# ThatKiteBot
ThatKiteBot is Discord bot focused on science commands and other fun stuff. 

# Section 1. Installing docker
The instructions below are for installing Docker specifically on **Debian Linux**, and will cover the current methods for adding Docker's official repos to your installation. **If you get stuck, reference [Docker's documentation](https://docs.docker.com/engine/install/) for the official instructions as this is distro-dependent and may not be up to date!**

If you are on a different distribution than Debian, please reference the aforementioned Docker docs, then skip to step 2. Note also that SELinux may cause issues and is not recommended for use with this project, nor is `wsl`.

### System requirements

It is recommended for the best experience that your host device has at least 4GB of RAM and is running Linux. It can be run on an absolute minimum of 2GB of RAM, though it may run out during longer runs. As for a CPU, bigger is better, though primarily the image commands are the only thing that should stress it. A Raspberry Pi 4 or 5 should be more than adequate in terms of computational power.

## 1.1 Preinstallation
Verify that you do not have the unnofficial Docker packages from Debian's default repositories installed.
```sh
sudo apt-get remove docker.io docker-doc docker-compose podman-docker containerd runc
```
This will likely result in no packages being removed, especially on a fresh install. This is to be expected, and according to the documentation will not remove any images, containers, volumes, or networks stored in `/var/lib/docker/`.

## 1.2 Installing from the official Docker repositories
This step will add Docker's repositories to `apt` and will import their signing key. Note that this does **NOT** work on other Debian-based distributions as `/etc/os-release` may cause it to behave incorrectly. 

If you are on a different distribution, substitute the line `$(. /etc/os-release && echo "$VERSION_CODENAME")` with the codename of the Debian release it is based on. As of the time of writing, this is most likely `bookworm` (current stable) or potentially `trixie` (current testing).
```sh
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```
To install the most recent version, run the following command:
```sh
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## 1.3 Verify the installation
To ensure everything installed correctly, run Docker's "Hello, world!" script.
```sh
sudo docker run hello-world
```

## 1.4 Check your docker compose verison
Make sure that your version of compose is at least 2.X by running `docker compose version`. Depending on the system, this command may have a hyphen and be formatted `docker-compose version`. It is also recommended for security that you add yourself to the docker group.
```sh
groupadd docker
usermod -aG docker $USER
```

# Section 2. Setup and first run

This will walk you through setting up and installing specifically the bot now that you have Docker installed. For the smoothest experience, you may want to set up a bot through Discord's Developer Portal prior to configuring the bot, however there is a simple guide later on that should get you through the basics. That said, you'll be on your own as far as authorizing it and adding it to your server.

## 2.1 Clone the repository
This will download the necessary files from GitHub for you to be able to build and run the Docker container.
```sh
git clone https://github.com/ThatRedKite/thatkitebot.git
```

## 2.2 Building the image
This will tell docker to grab all of the necessary dependencies and build the image, then run it. This step may take a while. Once it is completed, hit `ctrl+c` and you will be ready for the next step.
```sh
cd thatkitebot
sudo docker-compose up --build
```

## 2.3 Set API keys
Now you need to open up the bot's configuration file and give it a bot token so it can connect and run.
```sh
nano ./data/init_settings.json 
```
This will open the `nano` text editor where you will see something like this:
```json
{
    "discord token": "",
    "tenor api key": "",
    "prefix": "+",
}
```
`discord_token` is the discord bot API token you can get from the [Discord Developer Portal](https://discord.com/developers/) after making a bot. To do this, create an application, then go to the "bot" option in the settings bar to the left. From here, you'll generate a token and paste it inside the double quotes. Feel free to customize the bot while you're here - give it a name, profile picture, etc. **NEVER share your API keys** with **anyone**, and do **NOT** edit this file in the GitHub interface!

The tenor api key is not necessary for operation.

After that is done hit `ctrl + x`, `y` and `enter`. The settings will be saved.

## 2.4 Starting the bot 
Start the bot from a stopped state (like we have right now).
```sh
sudo docker-compose up -d thatkitebot
```
This will start the bot in the background. Error messages and status messages can be read with `docker logs thatkitebot-thatkitebot-1`. If you do not wish to start the bot in the background, you can omit the `-d` and any messages will be shown in your terminal.

# Section 3. Maintenance

## 3.1 Updating
To update, you will need to sync your local copy of the bot with the `git` repo and rebuild the container. This is required to get any potential missing libraries.
```sh
git pull
docker-compose up --build -d thatkitebot
```

To check the status of the container do `sudo docker container ls`. You should see 2 containers: `redis:alpine` and `thatkitebot_thatkitebot`. That will mean everything is running. Assuming everything is functioning correctly, congratulations, you should now have a functional bot and should see that the bot is online. To double check, you should respond to `+help` in your server (or alternatively replace the `+` with the prefix you set above).
## 3.2 Stopping
To stop the bot, run
```
sudo docker-compose stop
```

Made with ❤️
