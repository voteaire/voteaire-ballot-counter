## Proposer flow
* Proposer access main website
* Proposer connects wallet
* Proposer clicks on "Create Proposal"
* Proposer fills info about vote and submits
    * Proposal is validated against json schema then created in our DB via some post / create api call with status of 'created'
    * Wallet creates tranasction to create proposal onchain - user submits transaction
    * Hit API to update status to 'submitted transaction' + tx hash
    * frontend pools for status of proposal until it gets on-chain


## Voter flow
* Voter access main website
* Voter clicks on search bar and searches for proposal - /proposals
* Voter sees info about proposal including current vote results - /proposals/{proposal}
* Voter connects wallet (can be done before as well)
* Voter selects his choices and submits
* If voter is allowed to vote, he's prompted to sign tx
* Otherwise, message appears explaining the reason

Vote validation will be done in the front-end. If the vote is simple, no validation should be needed. If it's delegated, we should warn the user saying his voting power would be equal to how much he delegated to the pool at a specific time, we could point to some tool to help him verify that. If the vote is PolicyId based, we can use the serialization lib to confirm the user holds a valid token.

## Confirm flow
* User access main website
* User connects to wallet
* User clicks on "my votes" or maybe a profile - /user/{addr}
* User is presented will all his votes and proposals confirmed in the chain

## Counting Flow
* User access main website
* User clicks on search bar and searches for proposal - /proposals
* User sees that voting period has ended and clicks on see results - /proposals/{proposal}

I am worried about loading all proposals with /proposals, 1 year from now it could get really heavy. Maybe we should have some expire date where, after some time, the proposal is disconsidered (even to see the votes). It's also important to notice that anyone can create any proposal, so I could spam the network with 1k proposals with an end date of 2042. To prevent that we can limit the end date. And since we only validate proposals that transfered us some fee, a 10k profit from a spammer wouldn't be a problem.
