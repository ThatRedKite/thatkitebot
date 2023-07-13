## ThatKiteBot
A Discord bot focused on science commands and fun stuff. No moderation features for now.

## Installation and first run
The following instructions will be for a Debian system. **There can be problems if your system uses SELinux!!!**
(It is recommended that you [add yourself](https://docs.docker.com/engine/install/linux-postinstall/) to the docker user group to omit sudo for better security)
### Install docker:

```
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io
```
### Clone the repository
```
git clone https://github.com/ThatRedKite/thatkitebot.git
```
### Navigate to installed folder and start the docker container

```
cd thatkitebot
sudo docker-compose up --build
sudo docker-compose up
```
Docker will download all dependencies and start. This can take a while.
After it finishes starting hit `ctrl+c` to stop it and wait until it finishes.

### Set API keys
```
nano ./data/init_settings.json 
```
This will open nano editor where you will see something like this:
```json
{
    "discord token": "",
    "tenor api key": "",
    "prefix": "+"
}
```
The tenor token is optional. `discord_token` is the discord bot API token you can get from [discord](https://discord.com/developers/). `prefix` is what the bot will use as a command prefix for example `+` or `ex` or any other string or character. Don't forger to turn on `Privileged Gateway Intents` in the discord bot panel (next to the bot API token).

After that is done hit `ctrl + x`, `y` and `enter`. The settings will be saved.

### Starting the bot 
To start the bot from a stopped state (like we have right now).
```
sudo docker-compose up -d thatkitebot
```
You will see it print:
```
Starting redis ... done

Starting thatkitebot ... done
```
To check the status of the container do `sudo docker container ls` you will see 2 containers `redis:alpine` and `thatkitebot_thatkitebot` that means everything is running.
Now go to the server that you added the bot to and do +help (or whatever command prefix you chose) to see if it's working.
### Stopping
```
sudo docker-compose stop
```
