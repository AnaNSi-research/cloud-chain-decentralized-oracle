const Factory = artifacts.require('Factory');
const CloudSLA = artifacts.require('CloudSLA');
//const FileDigestOracle = artifacts.require('FileDigestOracle');
var myInstance;
//var oracleInstance;

contract('Factory', (accounts) => {
  it('CloudSLA creation and activation', async () => {
    //oracleInstance = await FileDigestOracle.deployed(); //.at("0xFa5B6432308d45B54A1CE1373513Fab77166436f");
    const instance = await Factory.deployed();
    const price = 5 * 10 ** 18; //5 ether in wei
    const monthlyValidityDuration = 30 * 24 * 60 * 60; //1 month in seconds
    const testValidityDuration = 60 * 60; //1 hour in seconds
    await instance.createChild(
      '0x481a80a8be21e55bc8c3e6d185eca762d3c3e2d8', //[CHAINLINK NODE ADDRESS HERE]
      accounts[1],
      String(price),
      String(testValidityDuration),
      1,
      1,
      { from: accounts[0] }
    );
    const scAddress = await instance.getSmartContractAddress(accounts[1], {
      from: accounts[1],
    });
    myInstance = await CloudSLA.at(scAddress);
    await myInstance.Deposit({ from: accounts[1], value: price });
    assert.equal(1, 1);
  });

  it('Upload', async () => {
    const hashDigest =
      '0x9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08';
    const challenge = web3.utils.keccak256(
      web3.eth.abi.encodeParameters(['bytes32'], [hashDigest]),
      { encoding: 'hex' }
    );

    //SLA Violation: undeleted file
    await myInstance.UploadRequest('test.pdf', challenge, {
      from: accounts[1],
    });
    await myInstance.UploadRequestAck('test.pdf', { from: accounts[0] });
    const res = await myInstance.UploadTransferAck('test.pdf', hashDigest, {
      from: accounts[0],
    });
    //await myInstance.UploadConfirm('test.pdf', true, { from: accounts[1] });
    assert.equal(1, 1);
  });

  it('Read', async () => {
    await myInstance.ReadRequest('test.pdf', { from: accounts[1] });
    await myInstance.ReadRequestAck('test.pdf', 'www.test.com', {
      from: accounts[0],
    });
    assert.equal(1, 1);
  });

  it('Delete', async () => {
    await myInstance.DeleteRequest('test.pdf', { from: accounts[1] });
    await myInstance.Delete('test.pdf', { from: accounts[0] });
    assert.equal(1, 1);
  });

  it('File check for undeleted file', async () => {
    const hashDigest = '0x1f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08';
    await myInstance.FileHashRequest('test.pdf', { from: accounts[1] });
    await myInstance.FileCheck('test.pdf', { from: accounts[1] });
    const requestID = await myInstance.FileCheck.call('test.pdf', { from: accounts[1] });
    await myInstance.onHashReceive(requestID, hashDigest, { from: accounts[1] });
    assert.equal(1, 1);
  });

  it('Another file upload', async () => {
    const hashDigest =
      '0x1f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08';
    const challenge = web3.utils.keccak256(
      web3.eth.abi.encodeParameters(['bytes32'], [hashDigest]),
      { encoding: 'hex' }
    );

    await myInstance.UploadRequest('test2.pdf', challenge, {
      from: accounts[1],
    });
    await myInstance.UploadRequestAck('test2.pdf', { from: accounts[0] });
    await myInstance.UploadTransferAck('test2.pdf', hashDigest, {
      from: accounts[0],
    });
    //await myInstance.UploadConfirm('test2.pdf', true, { from: accounts[1] });
    assert.equal(1, 1);
  });

  it('Read Deny with lost file check', async () => {
    await myInstance.ReadRequest('test2.pdf', { from: accounts[1] });
    await myInstance.ReadRequestDeny('test2.pdf', { from: accounts[0] });
    assert.equal(1, 1);
  });

  it('Another file upload + read', async () => {
    const hashDigest =
      '0x2f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08';
    const challenge = web3.utils.keccak256(
      web3.eth.abi.encodeParameters(['bytes32'], [hashDigest]),
      { encoding: 'hex' }
    );

    await myInstance.UploadRequest('test3.pdf', challenge, {
      from: accounts[1],
    });
    await myInstance.UploadRequestAck('test3.pdf', { from: accounts[0] });
    await myInstance.UploadTransferAck('test3.pdf', hashDigest, {
      from: accounts[0],
    });
    //await myInstance.UploadConfirm('test3.pdf', true, { from: accounts[1] });
    await myInstance.ReadRequest('test3.pdf', { from: accounts[1] });
    await myInstance.ReadRequestAck('test3.pdf', 'www.test3.com', {
      from: accounts[0],
    });
    assert.equal(1, 1);
  });

  it('File Check for corrupted file', async () => {
    const hashDigest = '0x4f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08';
    await myInstance.FileHashRequest('test3.pdf', { from: accounts[1] });
    const requestID = await myInstance.FileCheck.call('test3.pdf', { from: accounts[1] });
    await myInstance.onHashReceive(requestID, hashDigest, { from: accounts[1] });
    assert.equal(1, 1);
  });
});
