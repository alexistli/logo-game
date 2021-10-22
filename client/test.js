const crypto = require('crypto');
const _ = require('underscore');
const async = require('async');
const expect = require('expect');
const Client = require('./client');

const client = new Client(8124);
const verbose = false;

describe('Logo Game test', function () {
  it('should connect', done => {
    client.run(['coord'], (err, lines) => {
      expect(err).toNotExist();
      expect(lines).toEqual(['(15,15)']);

      done();
    });
  });

  it('should handle invalid commands', done => {
    client.run(['coord', 'invalid', 'coord'], (err, lines) => {
      expect(err).toNotExist();
      expect(lines).toEqual(['(15,15)', '(15,15)']);

      done();
    });
  });

  it('should render an empty canvas', done => {
    client.run(['render'], (err, lines) => {
      expect(err).toNotExist();
      expectLines(lines, 'cb431d3c0003b8c12210614ac123d25a53045ae3');

      done();
    });
  });

  it('should render a basic line', done => {
    client.run(['steps 5', 'render'], (err, lines) => {
      expect(err).toNotExist();
      expectLines(lines, 'e93477bbe56d53603973fd584b6227121a73b894');

      done();
    });
  });

  it('should render a basic shape', done => {
    client.run(['steps 5', 'right', 'steps 5', 'render'], (err, lines) => {
      expect(err).toNotExist();
      expectLines(lines, '94ff358ab3e2613010529d818681c766239e97f6');

      done();
    });
  });

  it('should move around', done => {
    client.run(['steps 3', 'right 2', 'steps 5', 'right 2', 'steps 6', 'right 2', 'steps 10', 'right 2', 'steps 6', 'right', 'steps 4', 'right', 'steps 6', 'render'], (err, lines) => {
      expect(err).toNotExist();
      expectLines(lines, 'ed3de7541b3362ebed1af5c7cd67290a46f52996');

      done();
    });
  });

  it('should draw multiple shapes', done => {
    client.run([
      'hover', 'steps 3', 'left 2', 'steps 6', 'draw', 'right 3', 'steps 6', 'right 2', 'steps 12', 'right 3', 'steps 24',
      'right 3', 'steps 6', 'right', 'steps 12', 'right 3', 'steps 6', 'right 2', 'steps 6',
      'render'
    ], (err, lines) => {
      expect(err).toNotExist();
      expectLines(lines, '9c9dd6c55072c25ef6d77e29d9a323439b10f0db');

      done();
    });
  });

  it('should draw multiple shapes concurrently', done => {
    async.parallel({
      shape1: next => client.run([
        'hover', 'left 2', 'steps 6', 'draw', 'right 3', 'steps 6', 'right 3', 'steps 12', 'render'
      ], next),

      shape2: next => client.run([
        'hover', 'left 2', 'steps 6', 'draw', 'right 2', 'steps 6', 'right 2', 'steps 10', 'left 5', 'steps 12', 'left 3', 'steps 14', 'render'
      ], next),

      shape3: next => client.run([
        'hover', 'steps 3', 'left', 'steps 6', 'draw', 'right 3', 'steps 12', 'right 3', 'steps 7', 'left 2', 'steps 7', 'right 3', 'steps 12', 'render'
      ], next)
    }, (err, results) => {
      expect(err).toNotExist();
      expectLines(results.shape1, '614ebd1ad5522b93b2d451c9f1925d630aae6468');
      expectLines(results.shape2, '7a1bb6ea2c522e1cede98c36df2bce977c1a62c5');
      expectLines(results.shape3, '86e06b9a36ab01d60e2fff29e0abda7b61b2bdba');

      done();
    })
  });

});

function expectLines(lines, fingerprint) {
  if (verbose)
    console.log(lines.join('\n'));

  expect(sha1(lines)).toEqual(fingerprint);
}

function sha1(lines) {
  var shasum = crypto.createHash('sha1');
  shasum.update(lines.join('\n'));

  return shasum.digest('hex');
};