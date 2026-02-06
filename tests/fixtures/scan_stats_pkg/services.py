"""Three services for scan stats counting."""

from dioxide import service


@service
class AlphaService:
    def run(self) -> str:
        return 'alpha'


@service
class BetaService:
    def run(self) -> str:
        return 'beta'


@service
class GammaService:
    def run(self) -> str:
        return 'gamma'
