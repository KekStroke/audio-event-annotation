export default {
  default: {
    paths: ["tests/bdd/**/*.feature"],
    requireModule: ["ts-node/register"],
    require: ["tests/bdd/steps/**/*.ts"],
    publishQuiet: true,
    format: ["progress"]
  }
};

