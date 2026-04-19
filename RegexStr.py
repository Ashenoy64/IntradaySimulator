import re

class RegexString( str ):
    def __new__( cls, value ):
        return super().__new__( cls, value )

    def __eq__( self, other ):
        if not isinstance( other, str ):
            return False
        return bool( re.fullmatch( str( self ), other ) )


    def __repr__( self ):
        return f"RegexString( { super().__str__()!r } )"
