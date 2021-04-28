@ECHO =============================
@ECHO Execute this on DevInstance
@ECHO   as: virtual.world\admin
@ECHO =============================
@REM


@REM Configure Red Team
@CALL net group /domain /delete red-team
@CALL net group /domain /add red-team

@CALL net user /domain /delete ralph
@CALL net user /domain /delete rachel

@CALL net user /domain /add ralph red-team1!
@CALL net user /domain /add rachel red-team1!

@CALL net group /domain /add red-team ralph
@CALL net group /domain /add red-team rachel

@REM Configure Blue Team
@CALL net group /domain /delete blue-team
@CALL net group /domain /add blue-team

@CALL net user /domain /delete betty
@CALL net user /domain /delete belle

@CALL net user /domain /add betty blue-team1!
@CALL net user /domain /add belle blue-team1!

@CALL net group /domain /add blue-team betty
@CALL net group /domain /add blue-team belle 

@REM Configure Green Team
@CALL net group /domain /delete green-team
@CALL net group /domain /add green-team

@CALL net user /domain /delete gary
@CALL net user /domain /add gary green-team1!

@CALL net group /domain /add green-team gary

