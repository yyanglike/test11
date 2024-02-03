import ssl
import asyncio
from urllib.parse import urlparse
from typing import Optional
from a1 import QuicConfiguration, H3Transport, connect, save_session_ticket
import httpx
from typing import cast
import time

H3_ALPN = ["h3"]

async def main(
    configuration: QuicConfiguration,
    url: str,
    data: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> None:
    # parse URL
    parsed = urlparse(url)
    assert parsed.scheme == "https", "Only https:// URLs are supported."
    host = parsed.hostname
    if parsed.port is not None:
        port = parsed.port
    else:
        port = 443

    while True:  # add an outer loop for reconnection
        try:
            connect_coroutine = connect(
                host,
                port,
                configuration=configuration,
                create_protocol=H3Transport,
                session_ticket_handler=save_session_ticket if save_session_ticket else None,
            )
            async with connect_coroutine as transport:
                while True:  # add an inner loop for periodic requests
                    try:
                        async with httpx.AsyncClient(
                            transport=cast(httpx.AsyncBaseTransport, transport)
                        ) as client:
                            # perform request
                            start = time.time()
                            if data is not None:
                                response = await client.post(
                                    url,
                                    content=data.encode(),
                                    headers={"content-type": "application/x-www-form-urlencoded"},
                                )
                            else:
                                try:
                                    response = await asyncio.wait_for(client.get(url), timeout=5.0)
                                except asyncio.TimeoutError:
                                    print("Connection timeout, reconnecting...")
                                    break

                            elapsed = time.time() - start
                            # print speed
                            octets = len(response.content)
                            print(
                                "Received %d bytes in %.1f s (%.3f Mbps)"
                                % (octets, elapsed, octets * 8 / elapsed / 1000000)
                            )
                            # print content
                            print("Content:", response.text)
                            await asyncio.sleep(10)  # sleep for 10 seconds

                    except Exception as e:
                        print("Error occurred during request:", e)
                        print("Reconnecting in 5 seconds...")
                        await asyncio.sleep(5)  # wait for 5 seconds before reconnection
                        break  # continue the inner loop to recreate the client

        except Exception as e:
            print("Error occurred during connection:", e)
            print("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)  # wait for 5 seconds before reconnection

if __name__ == "__main__":
    # prepare configuration
    configuration = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN)
    configuration.verify_mode = ssl.CERT_NONE  # do not validate server certificate
    url = "https://a.yd.com.cn:8443/api/endpoint1"
    asyncio.run(main(configuration, url))
