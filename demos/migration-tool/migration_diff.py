# Migration guide: rivet_di v1.x → dioxide v2.0
#
# Four find-and-replace patterns. That's it.
#
#   1. Package name
#      rivet_di             →  dioxide
#
#   2. Profile enum
#      ProfileEnum.PROD     →  Profile.PRODUCTION
#      ProfileEnum.TEST     →  Profile.TEST
#      ProfileEnum.DEV      →  Profile.DEVELOPMENT
#
#   3. Decorator API
#      @adapter.register()  →  @adapter.for_()
#
#   4. Container init
#      container = Container()           # same
#      container.scan(profile=Profile.PRODUCTION)
