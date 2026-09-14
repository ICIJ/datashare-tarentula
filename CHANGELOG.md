# CHANGELOG


## v4.5.2 (2026-09-14)

### Bug Fixes

- **tagging**: Accept /#/ds/ document URLs
  ([`0f1d56d`](https://github.com/ICIJ/datashare-tarentula/commit/0f1d56ddb537419c54d8b8b296f15a96b595ff40))

### Continuous Integration

- Auto-bump version and publish to PyPI on push to main
  ([`0bab686`](https://github.com/ICIJ/datashare-tarentula/commit/0bab68662882734cd57248bcd1f232dddcfc85c6))


## v4.5.1 (2026-05-07)

### Bug Fixes

- **client**: Apply CSRF token handling to all Datashare-routed requests
  ([`2190ebb`](https://github.com/ICIJ/datashare-tarentula/commit/2190ebbddcca32e041083d066af8aa0826bf364b))

### Build System

- **make**: Create annotated tags so git push --follow-tags pushes them
  ([`427918a`](https://github.com/ICIJ/datashare-tarentula/commit/427918afcac079ecd86a820f53bc511651f341ec))

### Refactoring

- **tagging**: Share CsrfState helper from datashare_client
  ([`f0d50be`](https://github.com/ICIJ/datashare-tarentula/commit/f0d50be87ac9129b6ae760be912fb15de53368f0))

### Testing

- **csrf**: Cover 403 retry, token caching, and direct-ES bypass
  ([`329e518`](https://github.com/ICIJ/datashare-tarentula/commit/329e51856f174edf27b0f0afee44732992b65729))


## v4.5.0 (2026-04-20)

### Documentation

- **readme**: Add manual fallback for PyPI and Docker publishing
  ([`6e2079d`](https://github.com/ICIJ/datashare-tarentula/commit/6e2079dc7a703350a2c18cc10d14d61321fa0241))

- **readme**: Rewrite release process around make bump-* and CI publishing
  ([`423d770`](https://github.com/ICIJ/datashare-tarentula/commit/423d77075dbb93e56c71898532e1e7f8c195c42e))


## v4.4.0 (2026-04-20)

### Bug Fixes

- Default sorting and order by
  ([`9f6c54e`](https://github.com/ICIJ/datashare-tarentula/commit/9f6c54e1fbcb9729902aa0ebb7c253a1fd43b4c6))

- **aggregate**: Catch requests ConnectionError and exit non-zero
  ([`2e2c866`](https://github.com/ICIJ/datashare-tarentula/commit/2e2c866aaf40aefe3f875b56d269664b149394e7))

- **cli**: Add spaces to multi-line help strings
  ([`69fa30f`](https://github.com/ICIJ/datashare-tarentula/commit/69fa30fb4676e864f48c1ba42355cccce6faf1d7))

- **client**: Deduplicate routing and refresh params in index
  ([`3e6f75e`](https://github.com/ICIJ/datashare-tarentula/commit/3e6f75e9336118cb2736faff7cb6ce94d97ed9cd))

- **client**: Default count query to match_all
  ([`258ad8b`](https://github.com/ICIJ/datashare-tarentula/commit/258ad8bb384ec198fd7d52f6e26388ee6ed9c71f))

- **client**: Drop read timeout for streamed downloads
  ([`3a29adc`](https://github.com/ICIJ/datashare-tarentula/commit/3a29adc1f27084d1f9e59bf7c4795a1d0e866e6b))

- **client**: Log CSRF token fetch failures at debug level
  ([`98b63fb`](https://github.com/ICIJ/datashare-tarentula/commit/98b63fb56b636f15167a52b0d0dcbba8b202d9f0))

- **client**: Release scroll context when scan_all completes
  ([`4f3044e`](https://github.com/ICIJ/datashare-tarentula/commit/4f3044eb47cb5b4019663f6a65f01337836728fe))

- **client**: Set a valid default Elasticsearch URL
  ([`c07e5f3`](https://github.com/ICIJ/datashare-tarentula/commit/c07e5f386cea003b7b416df96823dd4b7deecfb3))

- **client**: Stop creating index on construction
  ([`f6297cc`](https://github.com/ICIJ/datashare-tarentula/commit/f6297cc1adb385fc8f193a099d093d05846dbfe7))

- **client**: Store datashare_project arg on instance
  ([`1d646be`](https://github.com/ICIJ/datashare-tarentula/commit/1d646be37f17e29144dbfcd1c1c19385017c19b1))

- **config**: Correct /etc tarentula path typo
  ([`bc1c06b`](https://github.com/ICIJ/datashare-tarentula/commit/bc1c06b7ec7aa8827ac12ef85c29e2d4978bb3c5))

- **count**: Catch requests ConnectionError and exit non-zero
  ([`08872a0`](https://github.com/ICIJ/datashare-tarentula/commit/08872a09abf7ff0b8b9f09d3bb4997779e7f8fcc))

- **download**: Exit with non-zero code on connection failure
  ([`71d85c6`](https://github.com/ICIJ/datashare-tarentula/commit/71d85c605df914efd499daec98a2ce2f58a8f0d0))

- **download**: Respect --type when filtering raw files
  ([`ae556ed`](https://github.com/ICIJ/datashare-tarentula/commit/ae556edf7c3dd2a463af45233ac2c11487ba8495))

- **download**: Skip None source fields when --source is unset
  ([`40772b9`](https://github.com/ICIJ/datashare-tarentula/commit/40772b949010f146172220bc10fa5fc085a5db27))

- **export**: Exit with non-zero code on connection failure
  ([`a182fe3`](https://github.com/ICIJ/datashare-tarentula/commit/a182fe3a92f767276049ad60c2efa31fec30b947))

- **export**: Use QUOTE_ALL for CSV export
  ([`80ef68b`](https://github.com/ICIJ/datashare-tarentula/commit/80ef68bffae8e772af19d8f9e66e56d290d976ff))

- **graph**: Construct FuncAnimation only when rendering
  ([`e128112`](https://github.com/ICIJ/datashare-tarentula/commit/e1281128c6bbf9c057f93befe7f697f7e6ea4873))

- **graph**: Guard ys_param instead of xs_param
  ([`e45307c`](https://github.com/ICIJ/datashare-tarentula/commit/e45307cd8ebbe08678bd7b07c14550409d103284))

- **metadata_fields**: Catch requests ConnectionError and exit non-zero
  ([`200fdc4`](https://github.com/ICIJ/datashare-tarentula/commit/200fdc47d2a4f30a2ef61b432764a83f205d50b6))

- **metadata_fields**: Split filter pairs on first = only
  ([`46663a3`](https://github.com/ICIJ/datashare-tarentula/commit/46663a3ecb3ce054d5d6184999f7201963c4cf9e))

- **reindex**: Use max_docs param for Elasticsearch 8 compatibility
  ([`cec99f4`](https://github.com/ICIJ/datashare-tarentula/commit/cec99f4ee49bec611e5ae311bcff9500c8d510a7))

- **tag-cleaning**: Specify utf-8 encoding for query file
  ([`703a2c4`](https://github.com/ICIJ/datashare-tarentula/commit/703a2c49bf7d2b887f935339ead14b2eceb8c191))

- **tagging**: Refresh CSRF token on any 403 response
  ([`196fc79`](https://github.com/ICIJ/datashare-tarentula/commit/196fc7936fb9ce6b12f4fc1e9cf2aea70bb74d94))

### Build System

- **deps**: Bump matplotlib and drop Python 3.8 support
  ([`020b092`](https://github.com/ICIJ/datashare-tarentula/commit/020b092aa8c5c414ea486114130b6d22bf1854dd))

- **deps**: Bump pylint to ^3.0 for Python 3.12 compatibility
  ([`31cbacc`](https://github.com/ICIJ/datashare-tarentula/commit/31cbacc4530fca3aa4680f4c9d6cb98cf82c9665))

- **deps**: Refresh all transitive deps for Python 3.12 wheels
  ([`1d25dc8`](https://github.com/ICIJ/datashare-tarentula/commit/1d25dc84f98e58c77f22283f67185be30f739710))

- **docker**: Apply debian security upgrades during build
  ([`810b91a`](https://github.com/ICIJ/datashare-tarentula/commit/810b91a9ac0456f58745db58d189b4adfe4a44ff))

- **docker**: Bump base image to python 3.12 and poetry 2.1.1
  ([`0797423`](https://github.com/ICIJ/datashare-tarentula/commit/0797423fc3c2e4ca8e95a9dca26d755fd7f80d5e))

- **docker**: Enable pipefail for RUN pipelines
  ([`14e5d87`](https://github.com/ICIJ/datashare-tarentula/commit/14e5d87bc78f84511e6cf0934b0f0081c3172af6))

- **make**: Add bump-{patch,minor,major} targets with release hints
  ([`e748b71`](https://github.com/ICIJ/datashare-tarentula/commit/e748b713d9d92bfec1dcac9c80937dd366e93e30))

- **make**: Add self-documenting help target and lint rule
  ([`cd79f07`](https://github.com/ICIJ/datashare-tarentula/commit/cd79f076ce99934f86df6799c5b04892b7e88e65))

- **pytest**: Filter matplotlib pyparsing deprecation warnings
  ([`296cf37`](https://github.com/ICIJ/datashare-tarentula/commit/296cf379864b4bd75fb67d93c5fe2fcf41fe7e46))

### Code Style

- **cli**: Silence pylint no-value-for-parameter on click entry point
  ([`65f127c`](https://github.com/ICIJ/datashare-tarentula/commit/65f127cc153f6bb390bb71930c0a97f5b6729cfc))

- **docker**: Use ENV key=value syntax and drop undefined VENV_PATH
  ([`45e6992`](https://github.com/ICIJ/datashare-tarentula/commit/45e6992a8440e3262835b2d49da3eb1a2bad879c))

### Continuous Integration

- Add GitHub Actions CI workflow for lint and tests
  ([`f45a163`](https://github.com/ICIJ/datashare-tarentula/commit/f45a1631d72b2c365bcf7caa2d793be520b2f575))

- Add GitHub Actions release workflow for PyPI and Docker Hub
  ([`ad6a11d`](https://github.com/ICIJ/datashare-tarentula/commit/ad6a11d867fa2a7c87c28ae23839cafa3f497358))

- Bump datashare to 20.14.0
  ([`d1646f8`](https://github.com/ICIJ/datashare-tarentula/commit/d1646f8de072f07f88ce1fed849ba4aaa1e73759))

- Cancel in-progress CI runs on the same ref
  ([`d8d12b4`](https://github.com/ICIJ/datashare-tarentula/commit/d8d12b4fc5ce5414cc6b325dbe6c0d5d38d45a84))

- Delegate install, lint and test steps to Makefile
  ([`c9e05c8`](https://github.com/ICIJ/datashare-tarentula/commit/c9e05c8aa718f69aed7242c736af4fd65e1b2ffb))

- Remove CircleCI configuration in favor of GitHub Actions
  ([`3295373`](https://github.com/ICIJ/datashare-tarentula/commit/32953733b5dd6118cd8a1907c6dab421e39d112c))

- Scope workflow permissions to minimum required
  ([`8658eb5`](https://github.com/ICIJ/datashare-tarentula/commit/8658eb5a81b12bcf9e8b47dea41daca2448ecdac))

- Wait for Elasticsearch cluster health and extend Datashare retries
  ([`06bdab7`](https://github.com/ICIJ/datashare-tarentula/commit/06bdab72876a643147f7d01b54b736b0c06042e9))

- **release**: Drop unused poetry cache from pypi job
  ([`c12ae6c`](https://github.com/ICIJ/datashare-tarentula/commit/c12ae6cde050c4aec56414c0db6936a0adc34e46))

### Documentation

- **readme**: Replace CircleCI badge with GitHub Actions CI badge
  ([`11e0883`](https://github.com/ICIJ/datashare-tarentula/commit/11e088379657400a959122c757ab1175ef2317d0))

### Features

- Handle Datashare CSRF token on protected endpoints
  ([`10d3d9e`](https://github.com/ICIJ/datashare-tarentula/commit/10d3d9e818610a37d09d39feb3add2ef8e4426d0))

- **cli**: Accept both hyphen and underscore flag forms
  ([`0620353`](https://github.com/ICIJ/datashare-tarentula/commit/0620353bca1cd42fc64265c574a45c87aece1154))

### Performance Improvements

- **config**: Cache parsed ini contents
  ([`d40d4a7`](https://github.com/ICIJ/datashare-tarentula/commit/d40d4a73a25728e53b3c2c42f61c632452f92929))

- **tagging**: Cache CSV file reads
  ([`f7169b5`](https://github.com/ICIJ/datashare-tarentula/commit/f7169b564b18eb3c875944754a222289b5eaa5a3))

- **tagging-by-query**: Cache JSON file reads
  ([`181987d`](https://github.com/ICIJ/datashare-tarentula/commit/181987d18af3cc17cfa622e6ba46e15b8f7c6f79))

### Refactoring

- Address pylint 3.x warnings
  ([`0bfc7df`](https://github.com/ICIJ/datashare-tarentula/commit/0bfc7df9b76d2b36de2011161da4a6fa9a468a10))

- **aggregate**: Build agg spec in __init__ instead of property getter
  ([`376d47a`](https://github.com/ICIJ/datashare-tarentula/commit/376d47addc801316a3af668598051e4192a34d67))

- **cli**: Drop unreachable UsageError branch and None ctx arg
  ([`14749de`](https://github.com/ICIJ/datashare-tarentula/commit/14749de671d40e84bb93974c5f0c1c7729eaca74))

- **cli**: Use dispatch map for aggregate operation
  ([`a57df22`](https://github.com/ICIJ/datashare-tarentula/commit/a57df22a26ccacc8416ec6f8ce0daf5ec8d2e1b4))

- **client**: Drop unreachable return after contextmanager yield
  ([`765610c`](https://github.com/ICIJ/datashare-tarentula/commit/765610c428ac0c0743ec00bc1a55ee9987586529))

- **tagging**: Include HTTP status and response in error log
  ([`60b87eb`](https://github.com/ICIJ/datashare-tarentula/commit/60b87eb098fb1da65ed8a85265a45aaed1755edf))

### Testing

- Expose Elasticsearch build_flavor on TestAbstract
  ([`a0b26b8`](https://github.com/ICIJ/datashare-tarentula/commit/a0b26b8014ea61071a509e40e4c463a702e17f1e))

- **aggregate**: Skip string_stats on non-default Elasticsearch builds
  ([`a02f5ed`](https://github.com/ICIJ/datashare-tarentula/commit/a02f5ed56b526e6d48a91f8a296ab37793d6295e))

- **export**: Swap row order to match _score tiebreaker
  ([`3853930`](https://github.com/ICIJ/datashare-tarentula/commit/385393044274136924a0902ad9c2882953b5a0d2))

- **graph**: Hold GraphRealTime reference before calling add_point
  ([`9ca987b`](https://github.com/ICIJ/datashare-tarentula/commit/9ca987bea69723af6b7d9ee2058d078de1c5ab3e))

- **metadata**: Replace deprecated datetime.utcnow with timezone-aware now
  ([`c0e6920`](https://github.com/ICIJ/datashare-tarentula/commit/c0e6920c0e6642dc6af915e32fb5eba5cea88648))


## v4.3.6 (2024-06-13)

### Chores

- Lint datashare_client.py
  ([`40adca7`](https://github.com/ICIJ/datashare-tarentula/commit/40adca7437384e86e0fc5006e75fd396bf2f3376))


## v4.3.5 (2024-06-13)

### Bug Fixes

- Client count
  ([`5217374`](https://github.com/ICIJ/datashare-tarentula/commit/5217374e3bb1ba2931d66315db1f60b02c92dd58))

- Loosen Python version
  ([`821f605`](https://github.com/ICIJ/datashare-tarentula/commit/821f6057409762b3c84d2855fd982e693967499d))

- Loosen Python version
  ([`7a28a91`](https://github.com/ICIJ/datashare-tarentula/commit/7a28a9168af0e45e4cccfc0e51c1f93c01a24d30))

- Sorting by _score + test
  ([`fb8f167`](https://github.com/ICIJ/datashare-tarentula/commit/fb8f167de6511d94ee66477ab0a37fbece0d81ab))

### Features

- Add Duplicate to export-by-query type
  ([`e303cde`](https://github.com/ICIJ/datashare-tarentula/commit/e303cdebe930e6c3afffd9d15ed229c2b010cab6))


## v4.3.4 (2023-06-05)

### Bug Fixes

- 'is not' for string
  ([`6f5328e`](https://github.com/ICIJ/datashare-tarentula/commit/6f5328e513aaa125ad7668b2c514604b9e381c6f))

- Add escapechar in dictwriter call
  ([`6543f1f`](https://github.com/ICIJ/datashare-tarentula/commit/6543f1f9f808b4a27dd35527382fe3f2deac1e5e))

- Completing rebase master
  ([`0b6d055`](https://github.com/ICIJ/datashare-tarentula/commit/0b6d0552af63122031674da4d8a12401219d3595))

- Count limiting should not be there
  ([`8665b07`](https://github.com/ICIJ/datashare-tarentula/commit/8665b07568397549b0d7527317b0e408ee6d5c53))

- Docs and cli for #19
  ([`6055a9c`](https://github.com/ICIJ/datashare-tarentula/commit/6055a9cbe8cbfa1906ccefe45063ad977f3c18dc))

- Get back 'filter_by' param that got lost in conflicts
  ([`090631a`](https://github.com/ICIJ/datashare-tarentula/commit/090631abbb5c9ce99771ddedf70306a3d9d099af))

- Pr comments
  ([`e45ba69`](https://github.com/ICIJ/datashare-tarentula/commit/e45ba691174454fea678663905c583cc4a9baa98))

- Remove cli options accordingly to the unused constructor parameters
  ([`d19bf07`](https://github.com/ICIJ/datashare-tarentula/commit/d19bf07d0058d3d98cede4fbb2114f8f7872c53b))

- Remove logger calls
  ([`928a0e3`](https://github.com/ICIJ/datashare-tarentula/commit/928a0e376f7027754a9645f8786b4ff6676e5fae))

- Remove logging num of properties found
  ([`57e9a10`](https://github.com/ICIJ/datashare-tarentula/commit/57e9a10e43e06f36c006175cbd4208292d0e5515))

- Remove pending skip mentions
  ([`2c3fa34`](https://github.com/ICIJ/datashare-tarentula/commit/2c3fa348de4b93736ec06fa3c7ea2ff82d93b6c4))

- Remove print
  ([`17bddef`](https://github.com/ICIJ/datashare-tarentula/commit/17bddef942872c66a8a63b4653f33ee486106243))

- Remove query field from default values when disabled
  ([`15957ad`](https://github.com/ICIJ/datashare-tarentula/commit/15957adb4cb60e9b3ce3fd042317155548995b22))

- Remove remaining conflict
  ([`3edb07e`](https://github.com/ICIJ/datashare-tarentula/commit/3edb07e0ef7076e061d395982203eb3c12f69a75))

- Remove unnecesary csv
  ([`0123dd1`](https://github.com/ICIJ/datashare-tarentula/commit/0123dd12a5daee4a8855f9cd62ece787d4057e44))

- Remove unnecesary csv and ignore them from now on
  ([`2e84021`](https://github.com/ICIJ/datashare-tarentula/commit/2e84021c47a338b0de51d5b07b94c57dd0cdf752))

- Test in DS client with no default value in limit option
  ([`8efce7c`](https://github.com/ICIJ/datashare-tarentula/commit/8efce7c4eb8b01ab125433e59bf5c6368d870528))

- Tests and command in cli
  ([`a94ae8a`](https://github.com/ICIJ/datashare-tarentula/commit/a94ae8a4a6bc98bb1a8fcc13c656076d2642dbdc))

- Tests and command in cli
  ([`d35341b`](https://github.com/ICIJ/datashare-tarentula/commit/d35341b7209f013e646b16ba3eb2e038ab827056))

- The bash doc for CLI is highlighting shell keywords
  ([`a82a28b`](https://github.com/ICIJ/datashare-tarentula/commit/a82a28b888fd38deeb1b5d8bdc6863d606a3df50))

- Update quering url
  ([`4572f88`](https://github.com/ICIJ/datashare-tarentula/commit/4572f889658277d35141ee78ab9b6b8156e80ae6))

### Build System

- Restore docker push
  ([`73a06b6`](https://github.com/ICIJ/datashare-tarentula/commit/73a06b6b83261e93cb767c461fb8bcc674248560))

### Chores

- Add linter and remove lines too long
  ([`6741a3b`](https://github.com/ICIJ/datashare-tarentula/commit/6741a3bdabc50de71b3e81dc4759e8a99f6a551d))

- Add matplotlib to the dev dependencies
  ([`357fca4`](https://github.com/ICIJ/datashare-tarentula/commit/357fca428fcee0f1af5620ae5ac28a1aca655ffb))

- Lint aggregate.py
  ([`ee7cea3`](https://github.com/ICIJ/datashare-tarentula/commit/ee7cea3f5cf451b907efb9fe433f63986aa3ecbf))

- Lint cli.py
  ([`754d180`](https://github.com/ICIJ/datashare-tarentula/commit/754d1803c8bc7c149ea5c9daee703b8388c43088))

- Lint command.py
  ([`bf26f48`](https://github.com/ICIJ/datashare-tarentula/commit/bf26f489f380383e37dcc9fb5159e66c34f8679e))

- Lint config_file_reader
  ([`49d2459`](https://github.com/ICIJ/datashare-tarentula/commit/49d24594afc73087a75c6b580fb9ba041e491e1b))

- Lint count.py and pylintrc
  ([`13db2a8`](https://github.com/ICIJ/datashare-tarentula/commit/13db2a8b8bc252a1e0b5abecda895ce04be8dbf3))

- Lint datashare_client.py
  ([`61cf457`](https://github.com/ICIJ/datashare-tarentula/commit/61cf457b13d0a19588a21331952b17bae76ebecf))

- Lint download.py
  ([`0328c6b`](https://github.com/ICIJ/datashare-tarentula/commit/0328c6bb5ccd3d5ec2fdfbf94ad70443a6d976e7))

- Lint export_by_query.py
  ([`634c556`](https://github.com/ICIJ/datashare-tarentula/commit/634c55695da9cc9e01dd23f0141097c246d4ee4d))

- Lint graph_realtime.py
  ([`09499cc`](https://github.com/ICIJ/datashare-tarentula/commit/09499cc11e3e850e6d3175c051c4e66621329f02))

- Lint logger.py
  ([`4173683`](https://github.com/ICIJ/datashare-tarentula/commit/4173683d2406b2c14b6f909592f662b8e9480bf1))

- Lint metadata_fields.py
  ([`6d36a2d`](https://github.com/ICIJ/datashare-tarentula/commit/6d36a2db319914c7354fbb1d5cf49f7a5769f2e9))

- Lint tag_cleaning_by_query.py
  ([`af770ec`](https://github.com/ICIJ/datashare-tarentula/commit/af770ec020d48860f490a7f8e0d29d2fb1ff6ac0))

- Lint tagging.py
  ([`070923a`](https://github.com/ICIJ/datashare-tarentula/commit/070923a9b077f24ede684afa0ad20de1a77be3cb))

- Lint tagging_by_query.py
  ([`277f3c0`](https://github.com/ICIJ/datashare-tarentula/commit/277f3c03e8fffd34176367b9dbb7ff2f36392f23))

### Continuous Integration

- Add pylint to circleci
  ([`bcf444d`](https://github.com/ICIJ/datashare-tarentula/commit/bcf444dc48c36e926b24c5bcf24601afe41a532c))

- Fix path for pylint
  ([`e2f0cb9`](https://github.com/ICIJ/datashare-tarentula/commit/e2f0cb9c5efa4047cea2e936ecb6a3397b411265))

- Fix tests
  ([`c690999`](https://github.com/ICIJ/datashare-tarentula/commit/c690999087c3b948401660fb61f4d05238d9e173))

- Use Datashare 11.0.7
  ([`bf1e02c`](https://github.com/ICIJ/datashare-tarentula/commit/bf1e02c7825982f9b690a6a60040ca6498c29043))

- Use latest version of Datashare
  ([`0d36bec`](https://github.com/ICIJ/datashare-tarentula/commit/0d36bec4487045221aae258225ee395d007cc38e))

- Use python 3.10 on CI
  ([`06f6a45`](https://github.com/ICIJ/datashare-tarentula/commit/06f6a450de7f414d39ddc5f48ae5b43ec9ca6e99))

### Features

- Add date histogram aggregation
  ([`c7bf04d`](https://github.com/ICIJ/datashare-tarentula/commit/c7bf04d991f3f071237260ed6b8caac9f2227e39))

- Add date histogram aggregation
  ([`29de381`](https://github.com/ICIJ/datashare-tarentula/commit/29de381a5935703eefa556f225b388f10352b827))

- Add filter option to list_metadata cmd
  ([`ca812a0`](https://github.com/ICIJ/datashare-tarentula/commit/ca812a04b9a22e8b40ba2fd3ef34b081801e7a9a))

- Add filter option to list_metadata cmd
  ([`1fe30a3`](https://github.com/ICIJ/datashare-tarentula/commit/1fe30a3d7f22bdad8d4ab593b4db803939aca8e6))

- Add limit option to download command
  ([`2c9330c`](https://github.com/ICIJ/datashare-tarentula/commit/2c9330cd330980f5c598aa1470c9025cd72b76af))

- Add limit option to export-by-query command
  ([`0e9c1c0`](https://github.com/ICIJ/datashare-tarentula/commit/0e9c1c0bc8537def461300b32a51b8b9112fa994))

- Add limit option to export-by-query command
  ([`5fa2fd6`](https://github.com/ICIJ/datashare-tarentula/commit/5fa2fd6cf95f2eaa72d837873ff2ab01c94ed2f3))

- Add matplotlib to the dev dependencies
  ([`301254f`](https://github.com/ICIJ/datashare-tarentula/commit/301254f5dbfb5d8bdd76be0fa5bfdde15a9e993d))

Co-authored-by: Miguel Fiandor <miguelfg@users.noreply.github.com>

- Add metadata fields basic command
  ([`c1c6a7e`](https://github.com/ICIJ/datashare-tarentula/commit/c1c6a7e7b6b1ff2241a42b3307e9495148f08dd4))

Co-authored-by: Miguel Fiandor <miguelfg@users.noreply.github.com>

- Add metadata fields basic command
  ([`3cb4c50`](https://github.com/ICIJ/datashare-tarentula/commit/3cb4c508365af01f26a02993ad6ad9b24bf12192))

Co-authored-by: Miguel Fiandor <miguelfg@users.noreply.github.com>

- Add more kind of aggregations
  ([`0334000`](https://github.com/ICIJ/datashare-tarentula/commit/03340005dc5431a5d86400d85d84485819b2be2b))

- Add more kind of aggregations
  ([`87bfd27`](https://github.com/ICIJ/datashare-tarentula/commit/87bfd27f092317162f0c80926d0a6e367488ffaa))

- Add multi-platform support
  ([`9582896`](https://github.com/ICIJ/datashare-tarentula/commit/95828966d8c2a55270df1291e01975a183bebede))

- Add option skip to download, tested it in summary only
  ([`2604074`](https://github.com/ICIJ/datashare-tarentula/commit/26040746c3e7c9d1207ffe8f7486282ce9e6f5dd))

- Add option skip to download, tested it in summary only
  ([`8a9fa5b`](https://github.com/ICIJ/datashare-tarentula/commit/8a9fa5bf1b7bd7058bc21d229bc89e6bae041329))

- Add option skip to download, tested it in summary only
  ([`cb417e8`](https://github.com/ICIJ/datashare-tarentula/commit/cb417e8231e2d1e41256f7012562a5494d67a4aa))

- Add option skip to export-by-query and a test for option --size
  ([`c14a47f`](https://github.com/ICIJ/datashare-tarentula/commit/c14a47f5c3fbb651c8775de6d557a12fe81df42e))

- Add option skip to export-by-query and a test for option --size
  ([`7512293`](https://github.com/ICIJ/datashare-tarentula/commit/751229361807321601af19ec5ac218637bd849ec))

- Add sum aggregation
  ([`55bd784`](https://github.com/ICIJ/datashare-tarentula/commit/55bd7845bd44dc6acab1db5052677ca6065d6c74))

- Add sum aggregation
  ([`0504a04`](https://github.com/ICIJ/datashare-tarentula/commit/0504a040affbdc884d8ee98fddc66878d3e96560))

- Add test with multiple filters"
  ([`d744d35`](https://github.com/ICIJ/datashare-tarentula/commit/d744d356e6216a3586dcb1c2427721a2fb400612))

- Allow not to count all mapping properties
  ([`0697b06`](https://github.com/ICIJ/datashare-tarentula/commit/0697b06eeb8e7e450880b792b75b2391c50071e1))

- Allow not to count all mapping properties
  ([`53cff2a`](https://github.com/ICIJ/datashare-tarentula/commit/53cff2ac428ca8a08302dee2dd9fd51d39f2bf18))

- Enable list-metadata with remote Datashares
  ([`163f41d`](https://github.com/ICIJ/datashare-tarentula/commit/163f41d033dedb5fbb58744cc146957c545e11a9))

- Enable list-metadata with remote Datashares
  ([`7fe1e1b`](https://github.com/ICIJ/datashare-tarentula/commit/7fe1e1b41bea4673603ad5aa5f1a5c22945848cd))

- Nunique aggregation
  ([`edd6ce7`](https://github.com/ICIJ/datashare-tarentula/commit/edd6ce78c68c53f5f7a338886ce7bab46cc2bc52))

- Nunique aggregation
  ([`f19faa0`](https://github.com/ICIJ/datashare-tarentula/commit/f19faa013dfca2cb68cba1c3cba38b12b516c89e))

- Nunique aggregation
  ([`98badc7`](https://github.com/ICIJ/datashare-tarentula/commit/98badc766a35253cea9edbd30d0ce98050e18951))

- Start adding possibility of calculation number of unique values in field
  ([`aca3499`](https://github.com/ICIJ/datashare-tarentula/commit/aca3499b89b498f95d0f8167bcac4a00b07bb4b7))

- Start adding possibility of calculation number of unique values in field
  ([`5a03978`](https://github.com/ICIJ/datashare-tarentula/commit/5a0397837a37078c257c7984fb34e58754a11e4f))

- Start adding possibility of calculation number of unique values in field
  ([`5355243`](https://github.com/ICIJ/datashare-tarentula/commit/53552437efcd44c1e6d8fe0ccd486856f7b9bbbb))

- Use skip/from to ignore first n documents for download/export_by_query
  ([`73d9147`](https://github.com/ICIJ/datashare-tarentula/commit/73d91475f785cb766f7020850d237ae9645c89dd))

### Refactoring

- Add test and rename test names
  ([`7e63515`](https://github.com/ICIJ/datashare-tarentula/commit/7e635157cb79aedaaea6785c67df1581e26cffe4))

- Extract a command class
  ([`1fef0fe`](https://github.com/ICIJ/datashare-tarentula/commit/1fef0fe92fc181ff392b78f75cb3d83b3848e2b8))

- Improve naming test funcs
  ([`cfe436e`](https://github.com/ICIJ/datashare-tarentula/commit/cfe436ef91e65c49fd5d8caf8ee9628670c8f0c8))

- Introduce recursive function for getting field list #15
  ([`bd4463f`](https://github.com/ICIJ/datashare-tarentula/commit/bd4463f63adf629ffabfb0d66096cea6edd4ffb2))

- Move substraction of skip value to start function + remove commented lines
  ([`fd310b5`](https://github.com/ICIJ/datashare-tarentula/commit/fd310b536247dc3fd49c5b798afbeba3c2e19038))

- Move substraction of skip value to start function + remove commented lines
  ([`c47a1ce`](https://github.com/ICIJ/datashare-tarentula/commit/c47a1ce7725f6e5399fedafac87063b743131889))

- Move substraction of skip value to start function + remove commented lines
  ([`54f9c27`](https://github.com/ICIJ/datashare-tarentula/commit/54f9c274899737618565dddf101a8c086aff9b8a))

- Remove big common dataset and test with small ds per test
  ([`42b2477`](https://github.com/ICIJ/datashare-tarentula/commit/42b247710a440f9695e6bd322c0d02a769a190af))

- Remove dead code
  ([`5519745`](https://github.com/ICIJ/datashare-tarentula/commit/5519745b2e3e0ecc36c4aa602f7ddf9bf2111e27))

- Remove dead code
  ([`357c194`](https://github.com/ICIJ/datashare-tarentula/commit/357c194108332aec4326850e6ebdd7f3792d3d4d))

- Remove duplication of scan_or_query_all(...)
  ([`5b51d50`](https://github.com/ICIJ/datashare-tarentula/commit/5b51d503f2edff22619c3a5665964cef811519de))

- Rename agg name
  ([`31c4121`](https://github.com/ICIJ/datashare-tarentula/commit/31c4121cb7f24588b728a5e166f89cf4b1e2b949))

- Rename agg name
  ([`3854683`](https://github.com/ICIJ/datashare-tarentula/commit/3854683db6b40b4c338bcd1b18d6e18aee812d95))

- Rename agg name
  ([`2b914fe`](https://github.com/ICIJ/datashare-tarentula/commit/2b914fe7ff1ed89ababc794221a1f302cf325dc5))

- Rename agg name
  ([`2f7eba5`](https://github.com/ICIJ/datashare-tarentula/commit/2f7eba545b8884e8d678e7c73c95836f613ba1ab))

- Rename agg name
  ([`495d16f`](https://github.com/ICIJ/datashare-tarentula/commit/495d16f866cbf72422255ff5df857d71c301222e))

- Rename option
  ([`2b42e7a`](https://github.com/ICIJ/datashare-tarentula/commit/2b42e7a9ec5a981bb142d8c4584b2b9e0d335c48))

- Rename option
  ([`ffffba4`](https://github.com/ICIJ/datashare-tarentula/commit/ffffba4461c65b959be60ff0f017e7c1eab466dd))

- Rename option param name
  ([`51ada2b`](https://github.com/ICIJ/datashare-tarentula/commit/51ada2b0403d2c09adf8994030e1e05acfd9d1ca))

- Rename skip -> from
  ([`340ed9a`](https://github.com/ICIJ/datashare-tarentula/commit/340ed9a2df709f467f060377bc967758855c57fd))

### Testing

- Add property with ES version
  ([`115546c`](https://github.com/ICIJ/datashare-tarentula/commit/115546cdaef7a25c3ad9dee70cfbc8b2eb671ecc))

- Skip string_stats test on ES<7.11
  ([`80ca934`](https://github.com/ICIJ/datashare-tarentula/commit/80ca9344b48a2fe173b84ff79d0feadcb4088448))


## v4.3.3 (2022-12-15)

### Bug Fixes

- Cast stslog port type
  ([`961161d`](https://github.com/ICIJ/datashare-tarentula/commit/961161dc237808db04ab017176a668771158b950))

### Build System

- Add set_version target
  ([`b1bc135`](https://github.com/ICIJ/datashare-tarentula/commit/b1bc135fb4609050947d3fd875fe668497a637b6))

### Chores

- Maintenance upgrade
  ([`4033272`](https://github.com/ICIJ/datashare-tarentula/commit/4033272c66802286dfc70d417c30a1bae6a4f196))

- Migrate from nose to pytest
  ([`3c5ae11`](https://github.com/ICIJ/datashare-tarentula/commit/3c5ae11bcef20fad0349c65d598d282206f77e9b))


## v4.3.2 (2022-12-14)

### Bug Fixes

- Allows progress bar hidding
  ([`8d43e86`](https://github.com/ICIJ/datashare-tarentula/commit/8d43e865c2700494557d45cdcd155e4ff1b9046b))

- Avoid loading env path when empty
  ([`3170f6e`](https://github.com/ICIJ/datashare-tarentula/commit/3170f6e1f28bdcf319a5ff666d1b10f15bdfbcb4))

- Provide version to click explicitely
  ([`4b8fc9d`](https://github.com/ICIJ/datashare-tarentula/commit/4b8fc9d3e2edbf71b417bd98ab57656de4159f54))

- Remove 2 deps
  ([`a23b608`](https://github.com/ICIJ/datashare-tarentula/commit/a23b6087305fb96a76019c29ba27aa29818f7860))

- Remove link from title
  ([`6892c68`](https://github.com/ICIJ/datashare-tarentula/commit/6892c6870fb7239fc3f260054235f7011ede7ab1))

- Remove wrong indentation (added during refactor)
  ([`d900cb9`](https://github.com/ICIJ/datashare-tarentula/commit/d900cb989a65134f1c54ac11faf39cca6c617864))

- Search url should not contain _doc
  ([`0005121`](https://github.com/ICIJ/datashare-tarentula/commit/000512129f0b16d28d496add59435ae944b75992))

- Tests for Coun command
  ([`322c850`](https://github.com/ICIJ/datashare-tarentula/commit/322c85094a3ca54095f42b4eda0d4c9db48b8e8a))

- Toc link
  ([`c59d9dc`](https://github.com/ICIJ/datashare-tarentula/commit/c59d9dcd8e3e7db801d47475172649d184e855c9))

### Build System

- Add tagging shortcuts
  ([`962b859`](https://github.com/ICIJ/datashare-tarentula/commit/962b85917b93fa27ebf284afa75733d2e99340dd))

- Add version from poetry to Docker tagging
  ([`f326dd0`](https://github.com/ICIJ/datashare-tarentula/commit/f326dd089d64385d1f097ca815c1c3f9ae944a33))

- Migrate to Poetry
  ([`8a21e8c`](https://github.com/ICIJ/datashare-tarentula/commit/8a21e8c0e4273fd3f474bea46b09a1da5eff9c5f))

- Release version 4.3.1
  ([`7c3add4`](https://github.com/ICIJ/datashare-tarentula/commit/7c3add45408e9bff218f6131acaea0ecf6018f7e))

### Chores

- Add install requires to setup.py
  ([`ed0eb12`](https://github.com/ICIJ/datashare-tarentula/commit/ed0eb122ecb097d3b897cb6681cd97fb9fcc2335))

- Add tqdm for twine
  ([`8b55568`](https://github.com/ICIJ/datashare-tarentula/commit/8b555681b94900fd18591f03d12efc0fdd7e741c))

### Code Style

- Remove extract white-space before argument
  ([`a04c578`](https://github.com/ICIJ/datashare-tarentula/commit/a04c578f18670b86d5e52a0d373bfa9169c27d07))

- Remove useless comment
  ([`32e05be`](https://github.com/ICIJ/datashare-tarentula/commit/32e05be2dc7fb61f77a588ee91ff2e1f642b3055))

### Continuous Integration

- Install poetry without pip
  ([`9297908`](https://github.com/ICIJ/datashare-tarentula/commit/9297908dc33d8fa949f25eda751977de99f3948c))

- Save virtualenv artifacts
  ([`c298306`](https://github.com/ICIJ/datashare-tarentula/commit/c298306e7b7d8d1178f1ee82d9b6a9cdc01e0a2f))

- Specify poetry version and remove --with flag
  ([`88a3294`](https://github.com/ICIJ/datashare-tarentula/commit/88a32942283c4a3601a88b522426081d12d10af9))

- Split Poetry installation and package installation
  ([`f4d7276`](https://github.com/ICIJ/datashare-tarentula/commit/f4d7276bc0053d10d220c1d10c8eb8d2ba1cbca9))

- Swich to cimg image
  ([`d29b901`](https://github.com/ICIJ/datashare-tarentula/commit/d29b901c3b464eba50b957a54eac26995d0afe65))

- Switch back to circleci image
  ([`ef74c27`](https://github.com/ICIJ/datashare-tarentula/commit/ef74c27f79c2e25d9a5b49692042048c7e40689e))

### Documentation

- Add section about tag by query
  ([`001dfdf`](https://github.com/ICIJ/datashare-tarentula/commit/001dfdfb99662256f9263e391ee9f17418b4553a))

- Update download command interface
  ([`1312f94`](https://github.com/ICIJ/datashare-tarentula/commit/1312f94a626aa453cbfae1de5732713335d1cb9e))

### Features

- Add --wait-for-completion option
  ([`1492fc3`](https://github.com/ICIJ/datashare-tarentula/commit/1492fc34eb57451a57b5f112bceb043c59a9749f))

This option will use Elasticsearch build-in task manager to queue update opperation and return a
  list of created tasks.

- Add option to skip query field
  ([`82fc0ff`](https://github.com/ICIJ/datashare-tarentula/commit/82fc0ffa56b282faf08a3e287cb13e9848d6797e))

- Add size parameter for exportByQuery
  ([`bb48582`](https://github.com/ICIJ/datashare-tarentula/commit/bb48582778b2ccfe1c18b7eb11bea3a6699dcd03))

- Add sortBy and orderBy to download and export_by_query
  ([`77f037c`](https://github.com/ICIJ/datashare-tarentula/commit/77f037ccac82dc8be84fba4caee672a0a33c4837))

- Add support for configuration file
  ([`a32f7fb`](https://github.com/ICIJ/datashare-tarentula/commit/a32f7fb1f23ef37c553bd3f128aee6b33db831fb))

- Add support for source in export by query
  ([`1db055f`](https://github.com/ICIJ/datashare-tarentula/commit/1db055faa7eab3fbe76359eb84be8082271f41de))

- Add version option #4
  ([`05c81c6`](https://github.com/ICIJ/datashare-tarentula/commit/05c81c6e6ec84a1909b63e6f8f95e9fbf2eb81f0))

- Preserve csv fields order
  ([`fe490ca`](https://github.com/ICIJ/datashare-tarentula/commit/fe490cac16c2b3f313513ec5aa973b38a7dcf9dc))

- Replace tqdm by rich.progress
  ([`13c34fc`](https://github.com/ICIJ/datashare-tarentula/commit/13c34fc1e685cf598ec3572ea781675d0e3da3d8))

- Scroll option forces using the scroll api
  ([`5d21834`](https://github.com/ICIJ/datashare-tarentula/commit/5d218344f014bcbc640d405dcbf4357fb935f214))

BREAKING CHANGE: This modification allows a more explicite usage of the scroll API.

- Specify encoding
  ([`c6faa60`](https://github.com/ICIJ/datashare-tarentula/commit/c6faa60c1b5c6afba7fea0bfb1420eb80b8dc851))

- **tags**: Add `tagging_by_query` command
  ([`de5e34d`](https://github.com/ICIJ/datashare-tarentula/commit/de5e34df94c95cf54519524b9484b9c3b788356d))

This new command allows users to use a query (from a JSON file) to bulk tag documents

### Refactoring

- Remove description field (ignored by ES)
  ([`2b3918b`](https://github.com/ICIJ/datashare-tarentula/commit/2b3918ba609bcc370f88b0a4d76a3cd6a9e1d63f))

- Remove elasticsearch-py
  ([`ad14c4a`](https://github.com/ICIJ/datashare-tarentula/commit/ad14c4a4c2f6df632871dd8e43d8a51bba20653b))

- Remove unused import
  ([`dcce541`](https://github.com/ICIJ/datashare-tarentula/commit/dcce541cf1dcb61cd78572ce8687cc0cc16af28e))

- Remove unused import
  ([`3a6a151`](https://github.com/ICIJ/datashare-tarentula/commit/3a6a151033b486c2e296aee359b78a300adf01f7))

- Remove unused option
  ([`9bd8b6b`](https://github.com/ICIJ/datashare-tarentula/commit/9bd8b6b0ba93b77d4a803eecc7b6628a3c4da180))

- Remove unused option
  ([`5a6949b`](https://github.com/ICIJ/datashare-tarentula/commit/5a6949b0d0ee11c32f3de782982f275ba6070bb7))

- Use the same TestAbstract class as parent for each suite
  ([`3265900`](https://github.com/ICIJ/datashare-tarentula/commit/326590051640f4a09c677d78128893958b952d95))

- Use unique CSV fields
  ([`0f93eff`](https://github.com/ICIJ/datashare-tarentula/commit/0f93efffd8b892b9091ccb8c75996e941106c903))

### Testing

- Add missings packages for nose-watch
  ([`12d8e8c`](https://github.com/ICIJ/datashare-tarentula/commit/12d8e8cc5510b84d4cedfc6a25e23f2798c97525))

- Add nose-tests to watch changes while testing
  ([`7c328bb`](https://github.com/ICIJ/datashare-tarentula/commit/7c328bb22db6b0eb32a3a866cd76ec0bd2c81780))

- Add test for scan method
  ([`1b0840a`](https://github.com/ICIJ/datashare-tarentula/commit/1b0840ae4d0719c80adc999187d043c3a7111f80))

- Added unit test for download cli
  ([`40471a7`](https://github.com/ICIJ/datashare-tarentula/commit/40471a70aedc4bfe592c5639ffdfc4dd26fdcfc4))

- Move tearUp method to the right unit test class
  ([`73e10c2`](https://github.com/ICIJ/datashare-tarentula/commit/73e10c26564f52a99f11c269a5edc84839fc8074))

- Remove ./tmp directory after each test and fix doc ids
  ([`6d0350d`](https://github.com/ICIJ/datashare-tarentula/commit/6d0350dba113d2102571fff15979b165bfbb2764))

- Use isfile to ensure downloaded file exists
  ([`7c82ed8`](https://github.com/ICIJ/datashare-tarentula/commit/7c82ed8d2d469379f64632289076040af3561a2a))

- Use nosetests in Makefile
  ([`e03a43d`](https://github.com/ICIJ/datashare-tarentula/commit/e03a43d0e369a8096b0a6911954a7ebe57c7fc46))

- Use TemporaryDir instead of tmp
  ([`83d117b`](https://github.com/ICIJ/datashare-tarentula/commit/83d117b5091f7b9c52643807f238f21f033a060e))
