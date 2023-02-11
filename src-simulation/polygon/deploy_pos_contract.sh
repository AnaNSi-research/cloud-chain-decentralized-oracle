#!/bin/bash
cd ../staking-contracts 
npm run deploy  &> /dev/null
echo ------------------finish deploy------------------------------- 
npm run stake  &> /dev/null
echo ------------------finish stacking-------------------------------