// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
pragma experimental ABIEncoderV2;

import "./CloudSLA.sol";

contract Factory {
    mapping(address => address) private children; //from user to contract
    address private cloud;

    modifier OnlyCloud() {
        require(msg.sender == cloud, "OnlyCloud");
        _;
    }
    modifier Exists(address user) {
        require(children[user] != address(0), "Exists");
        _;
    }

    event ChildCreated(address childAddress, address _user);

    constructor() {
        cloud = msg.sender;
    }

    function createChild(
        address _oracle,
        address _user,
        uint256 _price,
        uint256 _validityDuration,
        uint256 lostFileCredits,
        uint256 undeletedFileCredits
    ) external OnlyCloud {
        CloudSLA child = new CloudSLA(
            _oracle,
            msg.sender,
            _user,
            _price,
            _validityDuration,
            lostFileCredits,
            undeletedFileCredits
        );
        children[_user] = address(child);
        emit ChildCreated(address(child), _user);
    }

    function getSmartContractAddress(address user)
        external
        view
        Exists(user)
        returns (address)
    {
        return children[user];
    }
}
