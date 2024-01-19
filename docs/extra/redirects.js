// redirects from the old sphinx docs site to the new

// redirects have to be done like this since anchor fragments aren't sent by the browser so server-side redirects
// wouldn't work

const lookup = {
  'install': '/install',
  'usage': '/usage/models/',
  'pep-484-types': '/usage/types/#typing-iterables',
  'id1': '/usage/dataclasses/',
  'nested-dataclasses': '/usage/dataclasses/#nested-dataclasses',
  'initialize-hooks': '/usage/dataclasses/#initialize-hooks',
  'choices': '/usage/types/#enums-and-choices',
  'validators': '/usage/validators/',
  'pre-and-per-item-validators': '/usage/validators/#pre-and-per-item-validators',
  'pre-and-whole-validators': '/usage/validators/#pre-and-per-item-validators',
  'validate-always': '/usage/validators/#validate-always',
  'root-validators': '/usage/validators/#root-validators',
  'id3': '/usage/validators/#root-validators',
  'dataclass-validators': '/usage/validators/#dataclass-validators',
  'field-checks': '/usage/validators/#field-checks',
  'recursive-models': '/usage/models/#recursive-models',
  'id4': '/usage/models/#recursive-models',
  'self-referencing-models': '/usage/postponed_annotations/#self-referencing-models',
  'self-ref-models': '/usage/postponed_annotations/#self-referencing-models',
  'generic-models': '/usage/models/#generic-models',
  'id5': '/usage/models/#generic-models',
  'orm-mode-aka-arbitrary-class-instances': '/usage/models/#orm-mode-aka-arbitrary-class-instances',
  'orm-mode': '/usage/models/#orm-mode-aka-arbitrary-class-instances',
  'schema-creation': '/usage/schema/',
  'schema': '/usage/schema/',
  'error-handling': '/usage/models/#error-handling',
  'datetime-types': '/usage/types/#datetime-types',
  'exotic-types': '/usage/types/',
  'booleans': '/usage/types/#booleans',
  'strictbool': '/usage/types/#booleans',
  'callable': '/usage/types/#callable',
  'urls': '/usage/types/#urls',
  'url-properties': '/usage/types/#url-properties',
  'international-domains': '/usage/types/#international-domains',
  'int-domains': '/usage/types/#international-domains',
  'underscores-in-hostnames': '/usage/types/#underscores-in-hostnames',
  'color-type': '/usage/types/#color-type',
  'secret-types': '/usage/types/#secret-types',
  'strict-types': '/usage/types/#strict-types',
  'json-type': '/usage/types/#json-type',
  'literal-type': '/usage/types/#literal-type',
  'payment-card-numbers': '/usage/types/#payment-card-numbers',
  'type-type': '/usage/types/#type',
  'custom-data-types': '/usage/types/#custom-data-types',
  'custom-root-types': '/usage/models/#custom-root-types',
  'custom-root': '/usage/models/#custom-root-types',
  'helper-functions': '/usage/models/#helper-functions',
  'model-config': '/usage/model_config/',
  'config': '/usage/model_config/',
  'alias-generator': '/usage/model_config/#alias-generator',
  'settings': '/usage/settings/',
  'id6': '/usage/settings/',
  'dynamic-model-creation': '/usage/models/#dynamic-model-creation',
  'usage-with-mypy': '/usage/mypy/',
  'usage-mypy': '/usage/mypy/',
  'strict-optional': '/usage/mypy/#strict-optional',
  'required-fields-and-mypy': '/usage/models/#required-fields',
  'usage-mypy-required': '/usage/models/#required-fields',
  'faux-immutability': '/usage/models/#faux-immutability',
  'exporting-models': '/usage/exporting_models/',
  'copying': '/usage/exporting_models/',
  'serialisation': '/usage/exporting_models/',
  'model-dict': '/usage/exporting_models/#modeldict',
  'dict-model-and-iteration': '/usage/exporting_models/#dictmodel-and-iteration',
  'model-copy': '/usage/exporting_models/#modelcopy',
  'model-json': '/usage/exporting_models/#modeljson',
  'json-dump': '/usage/exporting_models/#modeljson',
  'pickle-dumps-model': '/usage/exporting_models/#pickledumpsmodel',
  'pickle-serialisation': '/usage/exporting_models/#pickledumpsmodel',
  'advanced-include-and-exclude': '/usage/exporting_models/#advanced-include-and-exclude',
  'include-exclude': '/usage/exporting_models/#advanced-include-and-exclude',
  'custom-json-de-serialisation': '/usage/exporting_models/#custom-json-deserialisation',
  'json-encode-decode': '/usage/exporting_models/#custom-json-deserialisation',
  'abstract-base-classes': '/usage/models/#abstract-base-classes',
  'postponed-annotations': '/usage/postponed_annotations/',
  'id7': '/usage/postponed_annotations/',
  'id8': '/usage/postponed_annotations/',
  'usage-of-union-in-annotations-and-type-order': '/usage/types/#unions',
  'contributing-to-pydantic': '/contributing/',
  'pycharm-plugin': '/pycharm_plugin/',
  'id9': '/pycharm_plugin/',
  'history': '/changelog/',
}

function sanitizeURL(url) {
  // escape untrusted source by creating an anchor element and letting the browser parse it
  let a = document.createElement('a');
  a.href = url;
  return a.href;
}

function main() {
  const fragment = location.hash.substr(1).replace(/[^a-zA-Z0-9-_]/g, '') 
  if (fragment === '' || location.pathname !== '/') {
    // no fragment or not called from root
    return
  }
  let new_url = lookup[fragment]
  if (!new_url) {
    if (!fragment.startsWith('v')) {
      return
    }
    // change the fragments for versions - sphinx replaces dots with a dash while mkdocs removes dots
    new_url = '/changelog/#' + fragment
      .replace(/(v\d)-(\d+)-(\d+-\d{4})/, '$1$2$3')
      .replace(/(v\d)-(\d+-\d{4})/, '$1$2')
  }

  window.location = sanitizeURL(new_url)
}

main()
