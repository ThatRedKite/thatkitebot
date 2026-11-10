# ThatKiteBot - A Discord bot for science and nonsense

# Section 1. Installing docker
The instructions below are for installing Docker specifically on **Debian Linux**, and will cover official methods for adding Docker's repositories to your installation. Additionally, the addendum provides instructions for setup on Arch Linux, which TKB is developed on. **If you get stuck, reference [Docker's documentation](https://docs.docker.com/engine/install/)** - these instructions may not be up to date!

> 📝 **Note:** Systems utilizing SELinux (default under RHEL/Fedora and SUSE/openSUSE) or AppArmor (default under Ubuntu) may experience issues with Docker, and may experience breakages. It is additionally recommended to avoid `wsl`.

### System requirements:
It is recommended you run the bot with **no less** than 2GB of RAM, though for the best experience your host device should have at least 4GB. Raspberry Pi and other non-`amd64`/`x86_64` computers are currently unsupported, though this should be fixed soon.

## 1.1 Preinstallation
Verify that you do not have a third party packaged version of Docker installed from the Debian repos.
```sh
sudo apt-get remove docker.io docker-doc docker-compose podman-docker containerd runc
```
This will likely result in no packages being removed, especially on a fresh install - this is expected behavior. According to the documentation, if you were to have such a version installed, this will not remove any images, containers, volumes, or networks stored in `/var/lib/docker/`.

## 1.2 Installing from Docker's official repositories
This step will add Docker's repositories to `apt` and will import their signing key. 

If you are not on mainline Debian, substitute the line `$(. /etc/os-release && echo "$VERSION_CODENAME")` with the codename of the release it is based on. As of the time of writing, this is most likely `trixie` (current stable) or potentially `forky` (current development).
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

Now that the repos are configured, we can install Docker and its dependencies.
```sh
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## 1.3 Verify the installation
To ensure everything installed correctly, run Docker's "Hello, world!" script.
```sh
sudo docker run hello-world
```

## 1.4 Check your docker compose version
Before running, ensure you are running a Docker Compose version  of at least 2.X. Note that `docker compose` is fundamentally different from `docker-compose`, which executes a legacy (deprecated) version.
docker compose version

It is also recommended that you add yourself to the docker group for simplicity (though you should be aware of relevant [security implications](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user)).
```sh
groupadd docker
usermod -aG docker $USER
```

---

# Section 2. Setup and first run

This will walk you through setting up your bot now that you have Docker installed. For the smoothest experience, you may want to visit Discord's Developer Portal prior to configuring the bot, though there will be a simplified explanation later on that should roughly explain the basics of getting a bot token.

## 2.1 Clone the repository
The first step to getting everything running is to first pull in the TKB codebase from GitHub.
```sh
git clone https://github.com/ThatRedKite/thatkitebot.git
```

## 2.2 Building the image
The following command will tell docker to grab all of the necessary dependencies for the containers the bot uses and build the image. This step may take a while, and the bot should throw a token error at the end - this is to be expected as you haven't yet given it a bot token to run with. Once this occurs, your terminal should stop updating, and you should close the program with `ctrl+c` before proceeding to the next step.
```sh
cd thatkitebot
docker compose up --build
```

## 2.3 Set API keys
To get the bot connected and running, it needs a valid token. Open the config file in your editor of choice. We're opting to use `nano` as it is installed by default on most Linux distributions.
```sh
nano ./data/init_settings.json 
```
Inside of that file, you should see something like this:
```json
{
    "discord token": "",
    "tenor api key": "",
    "prefix": "+",
}
```
`discord_token` is the discord bot API token mentioned above, which you can get from the [Discord Developer Portal](https://discord.com/developers/). You should create an application, then go to the "bot" option in the settings bar to the left. From here, you'll generate a token and paste it inside the double quotes. 

> 📝 Note: Feel free to customize the bot while you're here - give it a name, profile picture, etc. 

### ⚠️ Warning: NEVER share your API keys with anyone, and do NOT edit this file in the GitHub interface! This will allow them direct access to your bot, and potential admin access to any servers it's in!

The tenor api key is not necessary for operation.
To save and exit, hit `ctrl + x`, `y`, and then `enter`. Your configuration should now be done!

## 2.4 Starting the bot 
Starting the bot at this point can be done with one last command.
```sh
docker compose up -d thatkitebot
```
This will launch the bot as a background process. If you would like to start it in the foreground (i.e. for debugging), you may omit the `-d` and any logs will be printed to the terminal. To view the logs, run:
```sh
docker logs thatkitebot-thatkitebot-1
```

---

# Section 3. Maintenance
For security and stability, it is advised to allot some downtime to updating the bot whenever a new release comes out. This will prevent breakage should a dependency change upstream and should give access to all the latest functionality.

## 3.1 Updating
To update, you will need to sync your local copy of the bot with the `git` repo and rebuild the container. This is required to fetch any potential missing or upgraded libraries.
```sh
git pull
docker compose up --build -d thatkitebot
```

To check the status of the container, run `docker container ls`. You should see 2 containers: `redis:alpine` and `thatkitebot_thatkitebot`. Assuming your config is set up correctly, you should now have an online and functional bot. To double check, you can run `+help` in your server (unless you set a different prefix in an above step).

## 3.2 Stopping
To stop the bot, run
```
docker compose stop
```

---

# Addendum: Unsupported and Partially Supported Platforms
As of the time of writing, Arch Linux is the only other supported distribution for the bot - and is the main one development is done on - though it will likely run on most others fine. Note that the method of installation is **NOT**, however, supported by Docker, and will involve third-party packaged software.

Additionally, Podman may be used as almost a drop-in replacement for Docker, though this is beyond the scope of this guide, and your mileage may vary.

## Arch Linux

Install the `docker` and `docker-compose` packages from the `Extra` repository.
```sh
sudo pacman -S docker docker-compose
```

Enable either the Docker service or socket. Enabling the service will start the daemon on boot, while the socket will allow it to be started whenever a container is run.
```sh
sudo systemctl enable docker.service
```
or
```sh
sudo systemctl enable docker.socket
```

Next, add yourself to the `docker` group to allow commands to run without `sudo` permissions.
```sh
groupadd docker
usermod -aG docker $USER
```

---

Made with ❤️
