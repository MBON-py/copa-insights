import streamlit as st

from models.profile import Profile

_PROFILE_KEY = "_auth_profile"


def get_profile() -> Profile | None:
    return st.session_state.get(_PROFILE_KEY)


def set_profile(profile: Profile) -> None:
    st.session_state[_PROFILE_KEY] = profile


def clear() -> None:
    st.session_state.pop(_PROFILE_KEY, None)


def is_authenticated() -> bool:
    return _PROFILE_KEY in st.session_state
