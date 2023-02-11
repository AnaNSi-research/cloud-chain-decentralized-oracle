#!/bin/bash
echo -n -e "Do you want create the network from zero? (yes/no)\n"
read VAR
declare -a addresses
declare -a node_ids


declare -i NUM_VALIDATORS=4
declare -i NUM_ACCOUNTS=120


if [ $VAR = "yes" ]
then
    
    
    
    
    echo -n -e "\nHow many validators do you want? (4, 8, 12)\n"
    read num
    NUM_VALIDATORS=$num
    
    rm -rf src
    mkdir src
    rm -rf polygon-network
    mkdir polygon-network
    mkdir polygon-network/tmp
    cd polygon-network
    
    for (( c=1; c<=$NUM_ACCOUNTS; c++ ))
    do
        ../bin/polygon-edge secrets init --data-dir node-$c >> ./tmp/out$c
    done
    
    for (( c=1; c<=$NUM_ACCOUNTS; c++ ))
    do
        INPUT=$(cat "./tmp/out$c")
        #Using as delimitator the = then focussing on the important data
        NODE_ID=$(echo $INPUT| cut -d'=' -f 3)
        TMP=$(echo $INPUT| cut -d'=' -f 2)
        ADDRESS=${TMP%N*}
        addresses[$c]=${ADDRESS// /} #removing white-space
        node_ids[$c]=${NODE_ID// /}
    done
    cd ..
    
    
    echo -n -e "\nWhich consensus mechanism do you want to use? (1-IBFT, 2-PoS)\n"
    read mechanism
    
    if (($mechanism==1))
    then
        mechanism='--consensus ibft'
        elif (($mechanism==2))
        then
        mechanism='--pos'
        if [ ! -d "./staking-contracts/" ] 
        then
            rm -rf staking-contracts
            echo -e \n\nDownloading resource files...\n\n
            git clone https://github.com/0xPolygon/staking-contracts.git
            cd staking-contracts
            echo -e \n\nInstalling node modules...\n\n
            npm i
            echo building contract...
            npm run build &> /dev/null
        else
            cd staking-contracts
        fi
        private_keys=''
        for (( c=1; c<=$NUM_VALIDATORS; c++ ))
        do
            private_keys="${private_keys} 0x$(cat '../polygon-network/node-'$c'/consensus/validator.key')"
            
            if (($c!=$NUM_VALIDATORS))
            then
                private_keys="${private_keys} ,"
            fi
        done
        echo -e "JSONRPC_URL=http://127.0.0.1:8545\nPRIVATE_KEYS=${private_keys}\nSTAKING_CONTRACT_ADDRESS=0x0000000000000000000000000000000000001001">.env
        cd ..
    else
        mechanism='--consensus ibft'
    fi
    cd polygon-network
    
    if [[ $mechanism == "--pos" ]]
    then
        epoch="--epoch-size 50"
    else
        epoch=''
    fi
    genesis="../bin/polygon-edge genesis --consensus ibft ${mechanism} ${epoch} --ibft-validators-prefix-path node- --bootnode '/ip4/127.0.0.1/tcp/11001/p2p/${node_ids[1]}' --bootnode '/ip4/127.0.0.1/tcp/12001/p2p/${node_ids[2]}'"
    
    
    for (( c=1; c<=$NUM_ACCOUNTS; c++ ))
    do
        
        genesis="${genesis} --premine=${addresses[c]}:1000000000000000000000"
        if (($c==$NUM_ACCOUNTS))
        then
            genesis="${genesis} --block-gas-limit 16234336 &> /dev/null"
        fi
    done
    eval $genesis


    
    #output file private_key
    private_keys='{"privatekey":['
    for (( c=1; c<=$NUM_ACCOUNTS; c++ ))
    do
        
        private_keys="${private_keys} \"0x$(cat './node-'$c'/consensus/validator.key')\""
        if (($c!=$NUM_ACCOUNTS))
        then
            private_keys="${private_keys} ,"
        fi
    done
    private_keys="${private_keys} ]}"
    echo $private_keys>../src/private_keys.json
    
    
    
    #output file address
    address='{"address":['
    for (( c=1; c<=$NUM_ACCOUNTS; c++ ))
    do
        address="${address} \"${addresses[$c]}\""
        if (($c!=$NUM_ACCOUNTS))
        then
            address="${address} ,"
        fi
    done
    address="${address} ]}"
    echo $address>../src/address.json
    rm -rf tmp
    echo -e "Network initialized correctly\n"
    
    
    for (( c=1; c<=$NUM_ACCOUNTS; c++ ))
    do
        rm -rf ./tmp/out$c
    done
else
    cd polygon-network
fi

for (( c=1; c<=$NUM_VALIDATORS; c++ ))
do
    tmp=$((c+9))
    command_run="${command_run} ../bin/polygon-edge server --data-dir ./node-${c} --chain genesis.json --grpc :${tmp}000 --libp2p :${tmp}001 --jsonrpc :${tmp}002 --seal &"
    if (($c==$NUM_VALIDATORS))
    then
        command_run="${command_run} ../bin/polygon-edge server --chain genesis.json --dev --log-level debug "
    fi
done

#echo $command_run
echo -n -e "Do you want run the newtork (yes/no)\n"
read VAR
if [ $VAR = "yes" ]
then
    if [[ $mechanism == "--pos" ]]
    then
        ../deploy_pos_contract.sh & cd ../polygon-network ; eval $command_run
    else
         eval $command_run
    fi
    
fi
