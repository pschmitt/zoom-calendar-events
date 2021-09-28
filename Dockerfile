FROM pschmitt/pyinstaller:3.9 as build
COPY requirements.txt zoom-gcal-events.py /app/
RUN STATICX=1 CLEAN=1 DIST_PATH=/dist /entrypoint.sh /app/zoom-gcal-events.py

FROM gcr.io/distroless/static-debian10
COPY --from=build /dist/zoom-gcal-events_static /zoom-gcal-events
VOLUME ["/config"]
ENV GCSA_CREDENTIALS=/config/credentials.json
ENTRYPOINT ["/zoom-gcal-events"]
