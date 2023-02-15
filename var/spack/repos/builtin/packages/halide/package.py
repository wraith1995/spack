# Copyright 2013-2022 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
from spack.package import *


class Halide(CMakePackage, PythonExtension):
    """Halide is a programming language designed to make it easier to write
    high-performance image and array processing code on modern machines."""

    homepage = "https://halide-lang.org/"
    url = "https://github.com/halide/Halide/archive/refs/tags/v14.0.0.tar.gz"
    git = "https://github.com/halide/Halide.git"
    maintainers = ["wraith1995"]
    version("main", branch="main")
    version("14.0.0", sha256="f9fc9765217cbd10e3a3e3883a60fc8f2dbbeaac634b45c789577a8a87999a01")
    variant(
        "build_type",
        default="Release",
        description="The build type to build",
        values=("Release", "Debug", "RelWithDebInfo"),
    )
    generator = "Ninja"
    variant("python", default=False, description="Install python bindings")
    variant("tutorials", default=False, description="Install the Halide Tutorials.")
    variant("utils", default=False, description="Install the Halide Utilities.")
    variant("tests", default=False, description="Build and Run Halide Tests and Apps.")
    extends("python", when="+python")
    _values = (
        "aarch64",
        "amdgpu",
        "arm",
        "hexagon",
        "nvptx",
        "powerpc",
        "riscv",
        "webassembly",
        "x86",
    )
    variant(
        "targets",
        default="arm,x86,nvptx,aarch64,hexagon,webassembly",
        description=("What targets to build. Spack's target family is always added "),
        values=_values,
        multi=True,
    )
    variant("sharedllvm", default=False, description="Link to the shared version of LLVM.")

    depends_on("cmake@3.22:", type="build")
    depends_on("ninja", type="build")
    depends_on(
        "llvm@14.0.0:14+clang+lld build_type=Release",
        type=("link", "run"),
    )
    for v in _values:
        depends_on("llvm targets={0}".format(v), type=("link", "run"), when="+{0}".format(v))
    depends_on("llvm+llvm_dylib+link_llvm_dylib", when="+sharedllvm")

    depends_on("libjpeg", type=("build", "link", "run"))
    depends_on("libpng", type=("build", "link", "run"))

    depends_on("python@3.8:", type=("build", "link", "run"), when="+python")
    # See https://github.com/halide/Halide/blob/main/requirements.txt
    depends_on("py-pybind11@2.6.2", type="build", when="+python")
    depends_on("py-setuptools@43:", type="build", when="+python")
    depends_on("py-scikit-build", type="build", when="+python")
    depends_on("py-wheel", type="build", when="+python")

    depends_on("py-imageio", type=("build", "run"), when="+python")
    depends_on("pil", type=("build", "run"), when="+python")
    depends_on("py-scipy", type=("build", "run"), when="+python")
    depends_on("py-numpy", type=("build", "run"), when="+python")

    @property
    def libs(self):
        return find_libraries("libHalide", root=self.prefix, recursive=True)

    def cmake_args(self):
        # See https://github.com/halide/Halide/blob/main/README_cmake.md#building-halide-with-cmake
        spec = self.spec
        llvm_config = spec["llvm"].llvm_config
        llvmdir = llvm_config("--cmakedir", output=str)
        args = [
            self.define("LLVM_DIR", llvmdir),
            self.define_from_variant("WITH_TESTS", "tests"),
            self.define_from_variant("WITH_TUTORIALS", "tutorials"),
            self.define_from_variant("WITH_UTILS", "utils"),
            self.define_from_variant("WITH_PYTHON_BINDINGS", "python"),
            self.define_from_variant("Halide_SHARED_LLVM", "sharedllvm"),
            self.define("WITH_WABT", False),
        ]
        llvm_targets = get_llvm_targets_to_build(spec)
        for target in llvm_targets:
            args += [self.define_from_variant("TARGET_{0}".format(target[0]), target[1])]

        if "+python" in spec:
            args += [
                self.define("Python3_EXECUTABLE", spec["python"].command.path),
                self.define("PYBIND11_USE_FETCHCONTENT", False),
                self.define(
                    "Halide_INSTALL_PYTHONDIR",
                    python_platlib,
                ),
            ]
        return args


def get_llvm_targets_to_build(spec):
    targets = spec.variants["targets"].value

    # Convert targets variant values to CMake LLVM_TARGETS_TO_BUILD array.
    spack_to_cmake = {
        "aarch64": "AArch64",
        "amdgpu": "AMDGPU",
        "arm": "ARM",
        "hexagon": "Hexagon",
        "nvptx": "NVPTX",
        "powerpc": "PowerPC",
        "riscv": "RISCV",
        "webassembly": "WebAssembly",
        "x86": "X86",
    }

    if spec.target.family in ("x86", "x86_64"):
        llvm_targets.add(("X86", True))
    elif spec.target.family == "arm":
        llvm_targets.add(("ARM", True))
    elif spec.target.family == "aarch64":
        llvm_targets.add(("AArch64", True))
    elif spec.target.family in ("ppc64", "ppc64le", "ppc", "ppcle"):
        llvm_targets.add(("PowerPC", True))

    # for everything not represented, we add False
    for v in spack_to_cmake.values():
        if (v, True) not in llvm_targets:
            llvm_targets.add((v, False))

    return list(llvm_targets)
