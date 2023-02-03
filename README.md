# Voteaire Ballot Counter

## How To Run It

This repository presents a docker compose file, which makes it very easy to run. Before using docker, though, you will need to setup the environment variables. Those are exemplified by our dotenv.sample file.

Important to notice that if you want to use mainnet, you will need to set the blockfrost project id and url to mainnet. Additionally, the docker-compose file has preprod nodes and kupo volumes instead of mainnet ones. You can remove them and use your own kupo instance or you can change them to their respective mainnet versions.

Finally, after environments are setup, you can run the following commands:

```
docker compose build
docker compose up
```

It will take some time for the node and kupo to synchronise. You can check their status with `http:localhost:1442/health` for kupo and `http:localhost:1337/health` for ogmios (which tells you the status of the node).