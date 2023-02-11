// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
pragma experimental ABIEncoderV2;

import "./FileDigestOracle.sol";

contract CloudSLA {
    address private oracle;
    address private user;
    address private cloud;

    struct Period {
        uint256 startTime;
        uint256 endTime;
    }

    enum Violation {
        lostFile,
        undeletedFile
    }

    struct Sla {
        bool paid;
        Period validityPeriod;
        uint256 credits;
    }

    enum State {
        defaultValue,
        uploadRequested,
        uploadRequestAck,
        uploadTransferAck,
        uploaded,
        deleteRequested,
        deleted,
        readRequested,
        readRequestAck,
        readDeny,
        checkRequested
    }

    struct File {
        bytes32 ID; //hash of filepath
        bool onCloud;
        State[] states;
        bytes32[] digests; //hashes of content
        string url; //last url
        bytes32 challenge; //hashes of the hash of the content
    }

    mapping(bytes32 => File) private files;
    uint256 price;
    mapping(Violation => uint256) violationCredits;
    uint256 validityDuration;
    Sla private currentSLA;

    function Hash(string memory str) private pure returns (bytes32) {
        return (sha256(abi.encodePacked(str)));
    }

    modifier OnlyUser() {
        require(msg.sender == user, "OnlyUser");
        _;
    }
    modifier OnlyCloud() {
        require(msg.sender == cloud, "OnlyCloud");
        _;
    }
    modifier OnlyUserOrCloud() {
        require((msg.sender == user || msg.sender == cloud), "OnlyUserOrCloud");
        _;
    }

    function FileInBC(bytes32 i) public view returns (bool res) {
        return (i != 0x0 && files[i].ID != 0x0);
    }

    function UrlPublished(bytes32 i) public view returns (bool res) {
        return (i != 0x0 &&
            files[i].ID != 0x0 &&
            bytes(files[i].url).length != 0);
    }

    function FileOnCloud(bytes32 i, bool onCloud)
        public
        view
        returns (bool res)
    {
        bool inBC = files[i].ID != 0x0;
        if (onCloud) return (i != 0x0 && inBC && files[i].onCloud);
        else return (!inBC || !files[i].onCloud);
    }

    function NotBeingChecked(bytes32 i) public view returns (bool res) {
        bool inBC = files[i].ID != 0x0;
        return (!inBC ||
            (files[i].states[files[i].states.length - 1] !=
                State.checkRequested));
    }

    function FileState(bytes32 i, State prevState)
        public
        view
        returns (bool res)
    {
        bool inBC = files[i].ID != 0x0;
        State lastState = files[i].states[files[i].states.length - 1];
        return (i != 0x0 && inBC && lastState == prevState);
    }

    modifier IsSLAValid() {
        require(
            block.timestamp >= currentSLA.validityPeriod.startTime &&
                block.timestamp <= currentSLA.validityPeriod.endTime,
            // use max_int only with go-quorum_raft instead of endTime
            //115792089237316195423570985008687907853269984665640564039457584007913129639935
            "SLAValidity"
        );
        _;
    }

    modifier Activatable(uint256 sentValue) {
        require(!currentSLA.paid && sentValue == price, "Activatable");
        _;
    }

    modifier ValidityPeriodEnded() {
        require(
            block.timestamp >= currentSLA.validityPeriod.endTime,
            "ValidityPeriodEnded"
        );
        _;
    }

    event Paid(address indexed _from, uint256 endTime);
    event CompensatedUser(address indexed _user, uint256 value);
    event PaidCloudProvider(address indexed _cloud, uint256 value);
    event UploadRequested(
        address indexed _from,
        string filepath,
        bytes32 challenge
    );
    event UploadRequestAcked(address indexed _from, string filepath);
    event UploadTransferAcked(
        address indexed _from,
        string filepath,
        bytes32 digest
    );
    event ChallengeCorrect(address indexed _from, string filepath);
    event ChallengeWrong(address indexed _from, bytes32 response);
    event DeleteRequested(address indexed _from, string filepath);
    event Deleted(address indexed _from, string filepath);
    event ReadRequested(address indexed _from, string filepath);
    event ReadRequestAcked(address indexed _from, string filepath, string url);
    event ReadRequestDenied(
        address indexed _from,
        string filepath,
        bool lostFile,
        uint256 credits
    );
    event FileChecked(
        address indexed _from,
        string filepath,
        string msg,
        uint256 credits
    );

    constructor(
        address _oracle,
        address _cloud,
        address _user,
        uint256 _price,
        uint256 _validityDuration,
        uint256 lostFileCredits,
        uint256 undeletedFileCredits
    ) {
        oracle = _oracle;
        cloud = _cloud;
        user = _user;
        price = _price;
        validityDuration = _validityDuration;
        violationCredits[Violation.lostFile] = lostFileCredits;
        violationCredits[Violation.undeletedFile] = undeletedFileCredits;
    }

    function Deposit() external payable OnlyUser Activatable(msg.value) {
        currentSLA.paid = true;
        currentSLA.validityPeriod.startTime = block.timestamp;
        currentSLA.validityPeriod.endTime = block.timestamp + validityDuration;
        emit Paid(msg.sender, currentSLA.validityPeriod.endTime);
    }

    function EndSla() external OnlyUserOrCloud ValidityPeriodEnded {
        CompensateUser();
        PayCloudProvider();
        delete currentSLA;
    }

    function CompensateUser() internal {
        uint256 value = currentSLA.credits < price ? currentSLA.credits : price;
        payable(user).transfer(value);
        emit CompensatedUser(user, value);
    }

    function PayCloudProvider() internal {
        uint256 value = address(this).balance;
        payable(cloud).transfer(value);
        emit PaidCloudProvider(cloud, value);
    }

    function UploadRequest(string calldata filepath, bytes32 challenge)
        external
        OnlyUser
        IsSLAValid
    {
        bytes32 i = Hash(filepath);
        require(FileOnCloud(i, false) && NotBeingChecked(i));
        files[i].ID = i;
        files[i].states.push(State.uploadRequested);
        files[i].challenge = challenge;
        emit UploadRequested(msg.sender, filepath, challenge);
    }

    function UploadRequestAck(string calldata filepath)
        external
        OnlyCloud
        IsSLAValid
    {
        bytes32 i = Hash(filepath);
        require(FileState(i, State.uploadRequested));
        files[i].states.push(State.uploadRequestAck);
        emit UploadRequestAcked(msg.sender, filepath);
    }

    function UploadTransferAck(string calldata filepath, bytes32 digest)
        external
        OnlyCloud
        IsSLAValid
    {
        bytes32 i = Hash(filepath);
        require(FileState(i, State.uploadRequestAck));
        files[i].states.push(State.uploadTransferAck);
        files[i].digests.push(digest);

        UploadConfirm(filepath, i, digest);

        emit UploadTransferAcked(msg.sender, filepath, digest);
    }

    function UploadConfirm(
        string calldata filepath,
        bytes32 index,
        bytes32 digest
    ) internal {
        bytes32 cloudResponse = keccak256(abi.encode(digest));
        if (files[index].challenge == cloudResponse) {
            files[index].states.push(State.uploaded);
            files[index].onCloud = true;
            emit ChallengeCorrect(msg.sender, filepath);
        } else {
            emit ChallengeWrong(msg.sender, cloudResponse);
            files[index].states.push(State.deleteRequested);
            emit DeleteRequested(msg.sender, filepath);
        }
    }

    function DeleteRequest(string calldata filepath)
        external
        OnlyUser
        IsSLAValid
    {
        bytes32 i = Hash(filepath);
        require(FileOnCloud(i, true) && NotBeingChecked(i));
        files[i].states.push(State.deleteRequested);
        emit DeleteRequested(msg.sender, filepath);
    }

    function Delete(string calldata filepath) external OnlyCloud IsSLAValid {
        bytes32 i = Hash(filepath);
        require(FileState(i, State.deleteRequested));
        files[i].states.push(State.deleted);
        files[i].onCloud = false;
        emit Deleted(msg.sender, filepath);
    }

    function ReadRequest(string calldata filepath)
        external
        OnlyUser
        IsSLAValid
    {
        bytes32 i = Hash(filepath);
        require(FileOnCloud(i, true) && NotBeingChecked(i));
        files[i].states.push(State.readRequested);
        emit ReadRequested(msg.sender, filepath);
    }

    function ReadRequestAck(string calldata filepath, string calldata url)
        external
        OnlyCloud
        IsSLAValid
    {
        bytes32 i = Hash(filepath);
        require(FileState(i, State.readRequested));
        files[i].states.push(State.readRequestAck);
        files[i].url = url;
        emit ReadRequestAcked(msg.sender, filepath, url);
    }

    function ReadRequestDeny(string calldata filepath)
        external
        OnlyCloud
        IsSLAValid
    {
        bytes32 i = Hash(filepath);
        require(FileState(i, State.readRequested));
        files[i].states.push(State.readDeny);
        emit ReadRequestDenied(
            msg.sender,
            filepath,
            LostFileCheck(i),
            currentSLA.credits
        );
    }

    function LostFileCheck(bytes32 ID) internal returns (bool) {
        bool lostFile = !OperationAfterUpload(ID, State.deleteRequested);
        if (lostFile) {
            currentSLA.credits =
                currentSLA.credits +
                violationCredits[Violation.lostFile];
        }
        return (lostFile);
    }

    function FileHashRequest(string calldata filepath)
        external
        OnlyUser
        IsSLAValid
    {
        bytes32 i = Hash(filepath);
        require(UrlPublished(i));
        FileDigestOracle(oracle).DigestRequest(files[i].url);
        if (files[i].states[files[i].states.length - 1] != State.checkRequested)
            files[i].states.push(State.checkRequested);
    }

    function FileCheck(string calldata filepath) external OnlyUser IsSLAValid {
        bytes32 i = Hash(filepath);
        require(FileInBC(i) && FileState(i, State.checkRequested));
        bool intactOnCloud = (files[i].digests[files[i].digests.length - 1] ==
            FileDigestOracle(oracle).DigestRetrieve(files[i].url));
        string memory res = "No SLA violations.";

        if (!files[i].onCloud && intactOnCloud) {
            res = "Cloud should have deleted the file but it did not.";
            currentSLA.credits =
                currentSLA.credits +
                violationCredits[Violation.undeletedFile];
        } else if (files[i].onCloud && !intactOnCloud) {
            res = "File has been corrupted.";
            currentSLA.credits =
                currentSLA.credits +
                violationCredits[Violation.lostFile];
        }
        //restore previous state
        files[i].states.push(files[i].states[files[i].states.length - 2]);
        emit FileChecked(msg.sender, filepath, res, currentSLA.credits);
    }

    //check if there is an operation after last upload
    function OperationAfterUpload(bytes32 ID, State operation)
        internal
        view
        returns (bool)
    {
        //get index of last uploaded state and last deleted state if present
        uint256 uploadedTime;
        uint256 operationTime;
        bool uploadedFound = false;
        bool operationFound = false;
        for (uint256 j = files[ID].states.length; j > 0; j--) {
            if (!operationFound && files[ID].states[j - 1] == operation) {
                operationTime = j - 1;
                operationFound = true;
            } else if (
                !uploadedFound && files[ID].states[j - 1] == State.uploaded
            ) {
                uploadedTime = j - 1;
                uploadedFound = true;
            }
            //early exit
            if (operationFound && uploadedFound) break;
        }
        return (operationFound && operationTime > uploadedTime);
    }

    function GetFile(string memory filepath)
        public
        view
        returns (
            bytes32,
            State[] memory,
            bool,
            bytes32[] memory,
            string memory
        )
    {
        bytes32 i = Hash(filepath);
        require(FileInBC(i));
        return (
            files[i].ID,
            files[i].states,
            files[i].onCloud,
            files[i].digests,
            files[i].url
        );
    }

    function GetSLAInfo()
        public
        view
        returns (
            bool,
            uint256,
            uint256,
            uint256
        )
    {
        return (
            currentSLA.paid,
            currentSLA.validityPeriod.startTime,
            currentSLA.validityPeriod.endTime,
            currentSLA.credits
        );
    }
}
